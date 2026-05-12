import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import type { BusinessContextProvider } from '../contracts/business-context-provider.contract';
import type { BusinessRetrievalInput } from '../contracts/business-retrieval-input.contract';
import type { BusinessRetrievalSlice } from '../contracts/business-retrieval-slice.contract';
import { RETRIEVAL_PROVIDER_ORDER } from '../policies/retrieval-access.policy';
import { YclientsAvailabilityService } from '../../../../shared/integrations/yclients/services/yclients-availability.service';
import { YclientsCatalogService } from '../../../../shared/integrations/yclients/services/yclients-catalog.service';
import { YclientsStaffService } from '../../../../shared/integrations/yclients/services/yclients-staff.service';

@Injectable()
export class YclientsAvailabilityBusinessContextProvider
  implements BusinessContextProvider
{
  readonly id = 'yclients.availability.snapshot';
  readonly scope = 'yclients.availability';
  readonly order = RETRIEVAL_PROVIDER_ORDER.YCLIENTS_AVAILABILITY;

  constructor(
    private readonly config: ConfigService,
    private readonly catalog: YclientsCatalogService,
    private readonly staff: YclientsStaffService,
    private readonly availability: YclientsAvailabilityService,
  ) {}

  async retrieve(input: BusinessRetrievalInput): Promise<BusinessRetrievalSlice> {
    const capturedAt = new Date().toISOString();
    const partner = (this.config.get<string>('yclients.partnerToken') ?? '').trim();
    const user = (this.config.get<string>('yclients.userToken') ?? '').trim();
    const company = (this.config.get<string>('yclients.companyId') ?? '').trim();
    if (!partner || !user || !company) {
      return {
        scope: this.scope,
        providerId: this.id,
        order: this.order,
        ok: true,
        capturedAt,
        unavailableReason: 'yclients_not_configured',
        facts: {},
      };
    }

    try {
      const services = await this.catalog.listServices(input.correlationId);
      const staffMembers = await this.staff.listStaff(input.correlationId);
      const nearestByService: Record<string, string> = {};
      const preview = services.slice(0, 3);
      let latestCapture = capturedAt;
      for (const s of preview) {
        const slot = await this.availability.getNearestSlot({
          serviceExternalId: s.externalId,
          fromIso: capturedAt,
          horizonDays: 5,
          correlationId: input.correlationId,
        });
        nearestByService[s.externalId] = slot?.startAtIso ?? 'none';
        if (slot?.startAtIso) {
          latestCapture = capturedAt;
        }
      }

      return {
        scope: this.scope,
        providerId: this.id,
        order: this.order,
        ok: true,
        capturedAt,
        facts: {
          availableServices: services.map((x) => ({
            id: x.externalId,
            title: x.title,
            durationMinutes: x.durationMinutes ?? null,
          })),
          staffNames: staffMembers.map((x) => ({
            id: x.externalId,
            name: x.displayName,
          })),
          nearestSlotStartByServiceId: nearestByService,
          availabilitySnapshotCapturedAt: latestCapture,
          availabilityNote:
            'read_only_cached_yclients_snapshot_may_be_stale_use_only_listed_slots',
        },
      };
    } catch {
      return {
        scope: this.scope,
        providerId: this.id,
        order: this.order,
        ok: false,
        capturedAt,
        unavailableReason: 'yclients_retrieval_failed',
        facts: {},
      };
    }
  }
}
