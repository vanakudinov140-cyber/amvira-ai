import { Injectable } from '@nestjs/common';
import type { BusinessContextProvider } from '../contracts/business-context-provider.contract';
import type { BusinessRetrievalInput } from '../contracts/business-retrieval-input.contract';
import type { BusinessRetrievalSlice } from '../contracts/business-retrieval-slice.contract';
import { RETRIEVAL_PROVIDER_ORDER } from '../policies/retrieval-access.policy';

/**
 * Booking list by dialog is not exposed on {@link BookingsService} without repository changes —
 * slice documents unavailability; no fabricated summaries.
 */
@Injectable()
export class BookingSummariesBusinessContextProvider implements BusinessContextProvider {
  readonly id = 'booking.summaries';
  readonly scope = 'booking.summaries';
  readonly order = RETRIEVAL_PROVIDER_ORDER.BOOKING_SUMMARIES;

  async retrieve(_input: BusinessRetrievalInput): Promise<BusinessRetrievalSlice> {
    const capturedAt = new Date().toISOString();
    return {
      scope: this.scope,
      providerId: this.id,
      order: this.order,
      ok: true,
      capturedAt,
      unavailableReason: 'booking_dialog_query_not_available',
      facts: {
        summaries: [] as const,
      },
    };
  }
}
