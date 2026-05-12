import { Injectable } from '@nestjs/common';
import type { BusinessContextProvider } from '../contracts/business-context-provider.contract';
import type { BusinessRetrievalInput } from '../contracts/business-retrieval-input.contract';
import type { BusinessRetrievalSlice } from '../contracts/business-retrieval-slice.contract';
import { RETRIEVAL_PROVIDER_ORDER } from '../policies/retrieval-access.policy';

@Injectable()
export class ScenarioSnapshotBusinessContextProvider implements BusinessContextProvider {
  readonly id = 'scenario.metadata';
  readonly scope = 'scenario.metadata';
  readonly order = RETRIEVAL_PROVIDER_ORDER.SCENARIO_METADATA;

  async retrieve(input: BusinessRetrievalInput): Promise<BusinessRetrievalSlice> {
    const capturedAt = new Date().toISOString();
    const code = input.scenarioCode?.trim();
    if (!code) {
      return {
        scope: this.scope,
        providerId: this.id,
        order: this.order,
        ok: true,
        capturedAt,
        unavailableReason: 'scenario_code_missing',
        facts: {},
      };
    }
    return {
      scope: this.scope,
      providerId: this.id,
      order: this.order,
      ok: true,
      capturedAt,
      facts: { scenarioCode: code },
    };
  }
}
