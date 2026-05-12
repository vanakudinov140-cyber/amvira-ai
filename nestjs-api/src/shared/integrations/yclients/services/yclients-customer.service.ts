import { Injectable } from '@nestjs/common';
import type { SalonCustomerV1 } from '../contracts/salon-domain.contract';
import { YclientsCompanyRestAdapter } from '../adapters/yclients-company-rest.adapter';
import {
  mapYclientsClientRow,
  unwrapYclientsData,
} from '../mappers/yclients-entity.mappers';

@Injectable()
export class YclientsCustomerService {
  constructor(private readonly adapter: YclientsCompanyRestAdapter) {}

  async findByPhone(input: {
    readonly phone: string;
    readonly correlationId?: string;
  }): Promise<readonly SalonCustomerV1[]> {
    const raw = await this.adapter.fetchClientsByPhoneJson({
      phone: input.phone,
      correlationId: input.correlationId,
    });
    const data = unwrapYclientsData(raw);
    const rows = Array.isArray(data) ? data : [];
    return rows
      .map((r) => mapYclientsClientRow(r))
      .filter((x): x is SalonCustomerV1 => x != null);
  }
}
