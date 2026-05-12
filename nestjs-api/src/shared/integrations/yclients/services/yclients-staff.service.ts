import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import type { SalonStaffMemberV1 } from '../contracts/salon-domain.contract';
import { YclientsReadThroughCacheService } from '../cache/yclients-read-through-cache.service';
import { YclientsCompanyRestAdapter } from '../adapters/yclients-company-rest.adapter';
import {
  mapYclientsStaffRow,
  unwrapYclientsData,
} from '../mappers/yclients-entity.mappers';

@Injectable()
export class YclientsStaffService {
  constructor(
    private readonly adapter: YclientsCompanyRestAdapter,
    private readonly cache: YclientsReadThroughCacheService,
    private readonly config: ConfigService,
  ) {}

  async listStaff(correlationId?: string): Promise<readonly SalonStaffMemberV1[]> {
    const cid = (this.config.get<string>('yclients.companyId') ?? '').trim();
    const key = this.cache.buildKey(['staff', 'members', cid]);
    const { value } = await this.cache.getOrSetJson<readonly SalonStaffMemberV1[]>(
      key,
      async () => {
        const raw = await this.adapter.fetchStaffJson(correlationId);
        const data = unwrapYclientsData(raw);
        const rows = Array.isArray(data) ? data : [];
        return rows
          .map((r) => mapYclientsStaffRow(r))
          .filter((x): x is SalonStaffMemberV1 => x != null);
      },
    );
    return value;
  }
}
