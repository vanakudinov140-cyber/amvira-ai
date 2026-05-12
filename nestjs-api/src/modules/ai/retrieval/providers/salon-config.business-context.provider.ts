import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import type { BusinessContextProvider } from '../contracts/business-context-provider.contract';
import type { BusinessRetrievalInput } from '../contracts/business-retrieval-input.contract';
import type { BusinessRetrievalSlice } from '../contracts/business-retrieval-slice.contract';
import { RETRIEVAL_PROVIDER_ORDER } from '../policies/retrieval-access.policy';

@Injectable()
export class SalonConfigBusinessContextProvider implements BusinessContextProvider {
  readonly id = 'salon.config';
  readonly scope = 'salon.config';
  readonly order = RETRIEVAL_PROVIDER_ORDER.SALON_CONFIG;

  constructor(private readonly config: ConfigService) {}

  async retrieve(_input: BusinessRetrievalInput): Promise<BusinessRetrievalSlice> {
    const capturedAt = new Date().toISOString();
    const displayName =
      this.config.get<string>('salon.displayName', '')?.trim() ?? '';
    if (!displayName) {
      return {
        scope: this.scope,
        providerId: this.id,
        order: this.order,
        ok: true,
        capturedAt,
        unavailableReason: 'salon_display_name_unconfigured',
        facts: {
          bookingPolicies: [
            'If yclients.availability slice is unavailable, do not invent services, staff, or slots.',
          ],
        },
      };
    }
    return {
      scope: this.scope,
      providerId: this.id,
      order: this.order,
      ok: true,
      capturedAt,
      facts: {
        displayName,
        bookingPolicies: [
          'Offer only services listed in yclients.availability/availableServices when that retrieval slice is ok.',
          'Offer only time slots present in yclients.availability/nearestSlotStartByServiceId or other explicit slot lists from the snapshot — never invent times.',
          'If yclients.availability slice is missing or unavailableReason is set, state that live availability is unknown and do not guess.',
          'Staff names must come only from yclients.availability/staffNames when present.',
        ],
      },
    };
  }
}
