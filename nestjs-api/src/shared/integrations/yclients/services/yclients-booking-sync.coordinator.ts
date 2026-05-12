import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { BookingsService } from '../../../../modules/bookings/bookings.service';
import { ClientsService } from '../../../../modules/clients/clients.service';
import type { SalonBookingRequestV1 } from '../contracts/salon-domain.contract';
import { YclientsIntegrationError } from '../errors/yclients-integration.error';
import { YclientsBookingService } from './yclients-booking.service';
import { YclientsCatalogService } from './yclients-catalog.service';

export type YclientsBookingSyncTelemetryV1 = Readonly<{
  readonly yclientsRequestMs: number;
  readonly syncOutcome: 'synced' | 'failed' | 'skipped' | 'not_attempted';
  readonly providerStatus:
    | 'healthy'
    | 'unavailable'
    | 'auth_failure'
    | 'rate_limited'
    | 'invalid_payload'
    | 'slot_conflict'
    | 'stale_availability'
    | 'unknown';
  readonly availabilityFreshness: string;
}>;

function providerStatusFromError(
  e: unknown,
): YclientsBookingSyncTelemetryV1['providerStatus'] {
  if (e instanceof YclientsIntegrationError) {
    switch (e.code) {
      case 'auth_failure':
        return 'auth_failure';
      case 'rate_limited':
        return 'rate_limited';
      case 'invalid_payload':
        return 'invalid_payload';
      case 'slot_conflict':
        return 'slot_conflict';
      case 'stale_availability':
        return 'stale_availability';
      case 'provider_unavailable':
        return 'unavailable';
      default:
        return 'unknown';
    }
  }
  return 'unknown';
}

@Injectable()
export class YclientsBookingSyncCoordinator {
  private readonly logger = new Logger(YclientsBookingSyncCoordinator.name);

  constructor(
    private readonly config: ConfigService,
    private readonly bookings: BookingsService,
    private readonly clients: ClientsService,
    private readonly catalog: YclientsCatalogService,
    private readonly yclientsBooking: YclientsBookingService,
  ) {}

  async syncAfterLocalBooking(input: Readonly<{
    readonly bookingId: string;
    readonly clientId: string;
    readonly serviceTitle: string;
    readonly datetimeIso: string;
    readonly notes?: string;
    readonly yclientsServiceId?: number;
    readonly yclientsStaffId?: number;
    readonly correlationId?: string;
  }>): Promise<YclientsBookingSyncTelemetryV1> {
    const enable = this.config.get<string | boolean>('yclients.enableSync') === true;
    const partner = (this.config.get<string>('yclients.partnerToken') ?? '').trim();
    const user = (this.config.get<string>('yclients.userToken') ?? '').trim();
    const company = (this.config.get<string>('yclients.companyId') ?? '').trim();
    if (!enable || !partner || !user || !company) {
      return {
        yclientsRequestMs: 0,
        syncOutcome: 'skipped',
        providerStatus: 'healthy',
        availabilityFreshness: 'not_applicable',
      };
    }

    const client = await this.clients.findOne(input.clientId);
    const phone = (client.phone ?? '').trim();
    if (!phone) {
      const msg = 'client_phone_required_for_yclients';
      await this.bookings.applyYclientsSync(input.bookingId, {
        syncStatus: 'failed',
        syncError: msg,
      });
      return {
        yclientsRequestMs: 0,
        syncOutcome: 'failed',
        providerStatus: 'invalid_payload',
        availabilityFreshness: 'not_applicable',
      };
    }

    let serviceExternal: string;
    if (input.yclientsServiceId != null && Number.isFinite(input.yclientsServiceId)) {
      serviceExternal = String(input.yclientsServiceId);
    } else {
      const resolved = await this.catalog.resolveServiceIdByTitle(
        input.serviceTitle,
        input.correlationId,
      );
      if (resolved == null) {
        const msg = `no_yclients_service_match:${input.serviceTitle}`;
        await this.bookings.applyYclientsSync(input.bookingId, {
          syncStatus: 'failed',
          syncError: msg,
        });
        return {
          yclientsRequestMs: 0,
          syncOutcome: 'failed',
          providerStatus: 'invalid_payload',
          availabilityFreshness: 'not_applicable',
        };
      }
      serviceExternal = String(resolved);
    }

    const staffExternal =
      input.yclientsStaffId != null && Number.isFinite(input.yclientsStaffId)
        ? String(input.yclientsStaffId)
        : undefined;

    const bookingRequest: SalonBookingRequestV1 = {
      version: 'salon.booking_request@v1',
      serviceExternalId: serviceExternal,
      staffExternalId: staffExternal,
      startAtIso: input.datetimeIso,
      comment: input.notes,
    };

    try {
      const { result, requestMs } = await this.yclientsBooking.createBooking(
        bookingRequest,
        {
          clientName: client.name,
          clientPhone: phone,
          correlationId: input.correlationId,
        },
      );
      await this.bookings.applyYclientsSync(input.bookingId, {
        externalId: result.externalRecordId,
        syncStatus: 'synced',
        syncError: null,
      });
      return {
        yclientsRequestMs: requestMs,
        syncOutcome: 'synced',
        providerStatus: 'healthy',
        availabilityFreshness: 'not_applicable',
      };
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      this.logger.warn(
        JSON.stringify({
          msg: 'yclients_booking_sync_failed',
          bookingId: input.bookingId,
          error: msg,
          correlationId: input.correlationId ?? null,
        }),
      );
      const status = providerStatusFromError(e);
      await this.bookings.applyYclientsSync(input.bookingId, {
        syncStatus: 'failed',
        syncError: msg.slice(0, 2000),
      });
      return {
        yclientsRequestMs: e instanceof YclientsIntegrationError ? 0 : 0,
        syncOutcome: 'failed',
        providerStatus: status,
        availabilityFreshness: 'not_applicable',
      };
    }
  }
}
