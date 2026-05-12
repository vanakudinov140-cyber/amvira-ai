import { Injectable, NotFoundException } from '@nestjs/common';
import { DialogsService } from '../../../dialogs/dialogs.service';
import type { BusinessContextProvider } from '../contracts/business-context-provider.contract';
import type { BusinessRetrievalInput } from '../contracts/business-retrieval-input.contract';
import type { BusinessRetrievalSlice } from '../contracts/business-retrieval-slice.contract';
import { RETRIEVAL_PROVIDER_ORDER } from '../policies/retrieval-access.policy';

@Injectable()
export class DialogSnapshotBusinessContextProvider implements BusinessContextProvider {
  readonly id = 'dialog.snapshot';
  readonly scope = 'dialog.snapshot';
  readonly order = RETRIEVAL_PROVIDER_ORDER.DIALOG_SNAPSHOT;

  constructor(private readonly dialogs: DialogsService) {}

  async retrieve(input: BusinessRetrievalInput): Promise<BusinessRetrievalSlice> {
    const capturedAt = new Date().toISOString();
    try {
      const d = await this.dialogs.findOne(input.dialogId);
      return {
        scope: this.scope,
        providerId: this.id,
        order: this.order,
        ok: true,
        capturedAt,
        facts: {
          dialogId: d.id,
          clientId: d.clientId,
          scenarioId: d.scenarioId,
          status: d.status,
          currentStageDb: d.currentStage,
          channelDb: d.channel,
          requestStage: input.currentStage,
          requestStatus: input.dialogStatus,
        },
      };
    } catch (e) {
      if (e instanceof NotFoundException) {
        return {
          scope: this.scope,
          providerId: this.id,
          order: this.order,
          ok: false,
          capturedAt,
          unavailableReason: 'dialog_not_found',
          facts: {},
        };
      }
      throw e;
    }
  }
}
