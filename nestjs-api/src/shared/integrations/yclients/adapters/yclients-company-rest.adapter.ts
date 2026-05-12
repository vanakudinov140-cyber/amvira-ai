import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { YclientsHttpClient } from '../client/yclients-http.client';

@Injectable()
export class YclientsCompanyRestAdapter {
  constructor(
    private readonly http: YclientsHttpClient,
    private readonly config: ConfigService,
  ) {}

  private companyId(): string {
    return (this.config.get<string>('yclients.companyId') ?? '').trim();
  }

  async fetchServicesJson(correlationId?: string): Promise<unknown> {
    const cid = this.companyId();
    const res = await this.http.requestJson<unknown>({
      method: 'GET',
      path: `services/${cid}/`,
      correlationId,
    });
    return res.data;
  }

  async fetchStaffJson(correlationId?: string): Promise<unknown> {
    const cid = this.companyId();
    const res = await this.http.requestJson<unknown>({
      method: 'GET',
      path: `staff/${cid}/`,
      correlationId,
    });
    return res.data;
  }

  async fetchBookTimesJson(input: {
    readonly staffId: number;
    readonly dateYmd: string;
    readonly serviceIds?: readonly number[];
    readonly correlationId?: string;
  }): Promise<unknown> {
    const cid = this.companyId();
    const query: Record<string, string | number | boolean | undefined> = {};
    if (input.serviceIds?.length) {
      query.service_ids = input.serviceIds.join(',');
    }
    const res = await this.http.requestJson<unknown>({
      method: 'GET',
      path: `book_times/${cid}/${input.staffId}/${input.dateYmd}`,
      query,
      correlationId: input.correlationId,
    });
    return res.data;
  }

  async fetchClientsByPhoneJson(input: {
    readonly phone: string;
    readonly correlationId?: string;
  }): Promise<unknown> {
    const cid = this.companyId();
    const res = await this.http.requestJson<unknown>({
      method: 'GET',
      path: `clients/${cid}`,
      query: { phone: input.phone, count: 20 },
      correlationId: input.correlationId,
    });
    return res.data;
  }

  async createRecordJson(input: {
    readonly body: Readonly<Record<string, unknown>>;
    readonly correlationId?: string;
  }): Promise<{ readonly data: unknown; readonly requestMs: number }> {
    const cid = this.companyId();
    const res = await this.http.requestJson<unknown>({
      method: 'POST',
      path: `records/${cid}`,
      body: input.body,
      correlationId: input.correlationId,
    });
    return { data: res.data, requestMs: res.requestMs };
  }

  async deleteRecordJson(input: {
    readonly recordId: number;
    readonly correlationId?: string;
  }): Promise<{ readonly data: unknown; readonly requestMs: number }> {
    const cid = this.companyId();
    const res = await this.http.requestJson<unknown>({
      method: 'DELETE',
      path: `record/${cid}/${input.recordId}`,
      correlationId: input.correlationId,
    });
    return { data: res.data, requestMs: res.requestMs };
  }
}
