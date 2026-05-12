import { Injectable } from '@nestjs/common';
import type { BusinessContextProvider } from '../contracts/business-context-provider.contract';
import type { BusinessRetrievalInput } from '../contracts/business-retrieval-input.contract';
import type { BusinessRetrievalSlice } from '../contracts/business-retrieval-slice.contract';
import { RETRIEVAL_PROVIDER_ORDER } from '../policies/retrieval-access.policy';

@Injectable()
export class StaticCatalogBusinessContextProvider implements BusinessContextProvider {
  readonly id = 'static.catalog';
  readonly scope = 'static.catalog';
  readonly order = RETRIEVAL_PROVIDER_ORDER.STATIC_CATALOG;

  async retrieve(_input: BusinessRetrievalInput): Promise<BusinessRetrievalSlice> {
    const capturedAt = new Date().toISOString();
    return {
      scope: this.scope,
      providerId: this.id,
      order: this.order,
      ok: true,
      capturedAt,
      facts: {
        serviceCategories: ['hair', 'nails', 'skin_care', 'brows'],
        note: 'static_category_labels_only_not_inventory',
      },
    };
  }
}
