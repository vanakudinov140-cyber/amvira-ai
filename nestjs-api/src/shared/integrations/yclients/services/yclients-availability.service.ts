import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import type { SalonAvailabilitySlotV1 } from '../contracts/salon-domain.contract';
import { YclientsReadThroughCacheService } from '../cache/yclients-read-through-cache.service';
import { YclientsCompanyRestAdapter } from '../adapters/yclients-company-rest.adapter';
import { mapBookTimesToSlots } from '../mappers/yclients-entity.mappers';
import { YclientsStaffService } from './yclients-staff.service';

export type YclientsAvailabilityQueryV1 = Readonly<{
  readonly serviceExternalId: string;
  readonly dateYmd: string;
  readonly staffExternalId?: string;
  readonly correlationId?: string;
}>;

function ymd(d: Date): string {
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

@Injectable()
export class YclientsAvailabilityService {
  constructor(
    private readonly adapter: YclientsCompanyRestAdapter,
    private readonly cache: YclientsReadThroughCacheService,
    private readonly config: ConfigService,
    private readonly staffService: YclientsStaffService,
  ) {}

  private companyId(): string {
    return (this.config.get<string>('yclients.companyId') ?? '').trim();
  }

  async getSlotsForStaffDay(input: YclientsAvailabilityQueryV1 & {
    readonly staffExternalId: string;
  }): Promise<{
    readonly slots: readonly SalonAvailabilitySlotV1[];
    readonly cacheHit: boolean;
    readonly capturedAtIso: string;
  }> {
    const sid = Number(input.staffExternalId);
    const svc = Number(input.serviceExternalId);
    if (!Number.isFinite(sid) || !Number.isFinite(svc)) {
      return { slots: [], cacheHit: false, capturedAtIso: new Date().toISOString() };
    }
    const cid = this.companyId();
    const key = this.cache.buildKey([
      'availability',
      cid,
      String(sid),
      input.dateYmd,
      String(svc),
    ]);
    const capturedAtIso = new Date().toISOString();
    const { value, cacheHit } = await this.cache.getOrSetJson<
      readonly SalonAvailabilitySlotV1[]
    >(key, async () => {
      const raw = await this.adapter.fetchBookTimesJson({
        staffId: sid,
        dateYmd: input.dateYmd,
        serviceIds: [svc],
        correlationId: input.correlationId,
      });
      return mapBookTimesToSlots(raw, String(sid), String(svc));
    });
    return { slots: value, cacheHit, capturedAtIso };
  }

  /**
   * Slots for a service on a date; when staff omitted, merges all staff (deduped by start time).
   */
  async getAvailableSlots(
    input: YclientsAvailabilityQueryV1,
  ): Promise<{
    readonly slots: readonly SalonAvailabilitySlotV1[];
    readonly cacheHit: boolean;
    readonly capturedAtIso: string;
  }> {
    const capturedAtIso = new Date().toISOString();
    if (input.staffExternalId) {
      return this.getSlotsForStaffDay({
        serviceExternalId: input.serviceExternalId,
        dateYmd: input.dateYmd,
        staffExternalId: input.staffExternalId,
        correlationId: input.correlationId,
      });
    }
    const staff = await this.staffService.listStaff(input.correlationId);
    const merged: SalonAvailabilitySlotV1[] = [];
    let anyHit = true;
    for (const s of staff) {
      const r = await this.getSlotsForStaffDay({
        serviceExternalId: input.serviceExternalId,
        dateYmd: input.dateYmd,
        staffExternalId: s.externalId,
        correlationId: input.correlationId,
      });
      if (!r.cacheHit) {
        anyHit = false;
      }
      merged.push(...r.slots);
    }
    const seen = new Set<string>();
    const deduped: SalonAvailabilitySlotV1[] = [];
    for (const sl of merged.sort(
      (a, b) => Date.parse(a.startAtIso) - Date.parse(b.startAtIso),
    )) {
      const k = `${sl.startAtIso}|${sl.staffExternalId ?? ''}`;
      if (!seen.has(k)) {
        seen.add(k);
        deduped.push(sl);
      }
    }
    return { slots: deduped, cacheHit: anyHit && staff.length > 0, capturedAtIso };
  }

  async getNearestSlot(input: {
    readonly serviceExternalId: string;
    readonly staffExternalId?: string;
    readonly fromIso: string;
    readonly horizonDays: number;
    readonly correlationId?: string;
  }): Promise<SalonAvailabilitySlotV1 | null> {
    const from = new Date(input.fromIso);
    if (Number.isNaN(from.getTime())) {
      return null;
    }
    const horizon = Math.min(Math.max(1, input.horizonDays), 30);
    const candidates: SalonAvailabilitySlotV1[] = [];
    for (let i = 0; i < horizon; i += 1) {
      const d = new Date(from);
      d.setUTCDate(d.getUTCDate() + i);
      const dateYmd = ymd(d);
      const { slots } = await this.getAvailableSlots({
        serviceExternalId: input.serviceExternalId,
        dateYmd,
        staffExternalId: input.staffExternalId,
        correlationId: input.correlationId,
      });
      for (const sl of slots) {
        if (Date.parse(sl.startAtIso) >= from.getTime()) {
          candidates.push(sl);
        }
      }
    }
    if (candidates.length === 0) {
      return null;
    }
    candidates.sort((a, b) => Date.parse(a.startAtIso) - Date.parse(b.startAtIso));
    return candidates[0] ?? null;
  }
}
