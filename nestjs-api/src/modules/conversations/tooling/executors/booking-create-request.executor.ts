import { Injectable } from '@nestjs/common';
import { BookingsService } from '../../../bookings/bookings.service';
import { YclientsBookingSyncCoordinator } from '../../../../shared/integrations/yclients/services/yclients-booking-sync.coordinator';
import type { SalesToolExecutor } from '../contracts/sales-tool-executor.contract';
import type { ToolExecutionContext, ToolExecutionItemResult } from '../contracts/tool-execution.contract';
import { isRecoverableToolError } from '../policies/tool-safe-execution.policy';

@Injectable()
export class BookingCreateRequestExecutor implements SalesToolExecutor {
  readonly toolId = 'booking.create_request' as const;

  constructor(
    private readonly bookings: BookingsService,
    private readonly yclientsSync: YclientsBookingSyncCoordinator,
  ) {}

  async execute(
    ctx: ToolExecutionContext,
    _params: Readonly<Record<string, unknown>>,
  ): Promise<ToolExecutionItemResult> {
    if (!ctx.bookingPayload) {
      return {
        intentId: ctx.activeIntentId,
        toolId: this.toolId,
        kind: 'skipped',
        detail: 'missing_booking_payload',
      };
    }
    try {
      const b = await this.bookings.create({
        clientId: ctx.clientId,
        service: ctx.bookingPayload.service,
        datetime: ctx.bookingPayload.datetime,
        notes: ctx.bookingPayload.notes,
      });
      const yc = await this.yclientsSync.syncAfterLocalBooking({
        bookingId: b.id,
        clientId: ctx.clientId,
        serviceTitle: ctx.bookingPayload.service,
        datetimeIso: new Date(ctx.bookingPayload.datetime).toISOString(),
        notes: ctx.bookingPayload.notes,
        yclientsServiceId: ctx.bookingPayload.yclientsServiceId,
        yclientsStaffId: ctx.bookingPayload.yclientsStaffId,
        correlationId: ctx.dialogId,
      });
      const refreshed = await this.bookings.findOne(b.id);
      return {
        intentId: ctx.activeIntentId,
        toolId: this.toolId,
        kind: 'success',
        payload: {
          bookingId: b.id,
          status: b.status,
          externalBookingId: refreshed.yclientsExternalId ?? null,
          syncStatus: refreshed.yclientsSyncStatus ?? null,
          syncError: refreshed.yclientsSyncError ?? null,
          yclients: {
            yclientsRequestMs: yc.yclientsRequestMs,
            syncOutcome: yc.syncOutcome,
            providerStatus: yc.providerStatus,
            availabilityFreshness: yc.availabilityFreshness,
          },
        },
      };
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      return {
        intentId: ctx.activeIntentId,
        toolId: this.toolId,
        kind: 'failed',
        detail: msg,
        recoverability: isRecoverableToolError(e)
          ? 'recoverable'
          : 'non_recoverable',
      };
    }
  }
}
