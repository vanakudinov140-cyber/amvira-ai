import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import type { SalonServiceV1 } from '../contracts/salon-domain.contract';
import { YclientsReadThroughCacheService } from '../cache/yclients-read-through-cache.service';
import { YclientsCompanyRestAdapter } from '../adapters/yclients-company-rest.adapter';
import {
  mapYclientsServiceRow,
  unwrapYclientsData,
} from '../mappers/yclients-entity.mappers';

@Injectable()
export class YclientsCatalogService {
  constructor(
    private readonly adapter: YclientsCompanyRestAdapter,
    private readonly cache: YclientsReadThroughCacheService,
    private readonly config: ConfigService,
  ) {}

  async listServices(
    correlationId?: string,
  ): Promise<readonly SalonServiceV1[]> {
    const cid = (this.config.get<string>('yclients.companyId') ?? '').trim();
    const key = this.cache.buildKey(['catalog', 'services', cid]);
    const { value } = await this.cache.getOrSetJson<readonly SalonServiceV1[]>(
      key,
      async () => {
        const raw = await this.adapter.fetchServicesJson(correlationId);
        const data = unwrapYclientsData(raw);
        const rows = Array.isArray(data) ? data : [];
        return rows
          .map((r) => mapYclientsServiceRow(r))
          .filter((x): x is SalonServiceV1 => x != null);
      },
    );
    return value;
  }

  async resolveServiceIdByTitle(
    title: string,
    correlationId?: string,
  ): Promise<number | null> {
    const needle = title.trim().toLowerCase();
    if (!needle) {
      return null;
    }
    const list = await this.listServices(correlationId);
    const hit = list.find((s) => s.title.trim().toLowerCase() === needle);
    return hit ? Number(hit.externalId) : null;
  }
}
