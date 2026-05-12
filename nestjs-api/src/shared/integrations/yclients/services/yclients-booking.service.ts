import { Injectable } from '@nestjs/common';
import type {
  SalonBookingRequestV1,
  SalonBookingResultV1,
} from '../contracts/salon-domain.contract';
import { YclientsCompanyRestAdapter } from '../adapters/yclients-company-rest.adapter';
import { mapRecordCreateToSalonBookingResult } from '../mappers/yclients-entity.mappers';

export type YclientsCreateBookingContextV1 = Readonly<{
  readonly clientName: string;
  readonly clientPhone: string;
  readonly correlationId?: string;
}>;

@Injectable()
export class YclientsBookingService {
  constructor(private readonly adapter: YclientsCompanyRestAdapter) {}

  async createBooking(
    request: SalonBookingRequestV1,
    ctx: YclientsCreateBookingContextV1,
  ): Promise<{ readonly result: SalonBookingResultV1; readonly requestMs: number }> {
    const serviceId = request.serviceExternalId
      ? Number(request.serviceExternalId)
      : NaN;
    const staffId = request.staffExternalId
      ? Number(request.staffExternalId)
      : undefined;
    if (!Number.isFinite(serviceId)) {
      throw new Error('invalid_service_external_id');
    }
    const dt = new Date(request.startAtIso);
    if (Number.isNaN(dt.getTime())) {
      throw new Error('invalid_start_at');
    }
    const body: Record<string, unknown> = {
      services: [{ id: serviceId, quantity: 1 }],
      client: {
        name: ctx.clientName,
        phone: ctx.clientPhone.replace(/\D/g, '') || ctx.clientPhone,
      },
      datetime: dt.toISOString(),
      send_sms: false,
      attendance: 0,
    };
    if (staffId != null && Number.isFinite(staffId)) {
      body.staff_id = staffId;
    }
    if (request.comment) {
      body.comment = request.comment;
    }
    const { data, requestMs } = await this.adapter.createRecordJson({
      body,
      correlationId: ctx.correlationId,
    });
    return { result: mapRecordCreateToSalonBookingResult(data), requestMs };
  }

  async cancelRecord(
    recordId: number,
    correlationId?: string,
  ): Promise<{ readonly requestMs: number }> {
    const { requestMs } = await this.adapter.deleteRecordJson({
      recordId,
      correlationId,
    });
    return { requestMs };
  }
}
