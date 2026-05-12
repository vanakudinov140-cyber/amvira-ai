import { Injectable, NotFoundException } from '@nestjs/common';
import { MessagesService } from '../../../messages/messages.service';
import type { BusinessContextProvider } from '../contracts/business-context-provider.contract';
import type { BusinessRetrievalInput } from '../contracts/business-retrieval-input.contract';
import type { BusinessRetrievalSlice } from '../contracts/business-retrieval-slice.contract';
import { RETRIEVAL_PROVIDER_ORDER } from '../policies/retrieval-access.policy';

const MAX_MESSAGES = 15;

@Injectable()
export class RecentMessagesBusinessContextProvider implements BusinessContextProvider {
  readonly id = 'recent.messages';
  readonly scope = 'recent.messages';
  readonly order = RETRIEVAL_PROVIDER_ORDER.RECENT_MESSAGES;

  constructor(private readonly messages: MessagesService) {}

  async retrieve(input: BusinessRetrievalInput): Promise<BusinessRetrievalSlice> {
    const capturedAt = new Date().toISOString();
    try {
      const list = await this.messages.listByDialog(input.dialogId);
      const tail = list.slice(-MAX_MESSAGES);
      const turns = tail.map((m) => ({
        role: m.role,
        content: m.content,
        at: m.createdAt.toISOString(),
      }));
      return {
        scope: this.scope,
        providerId: this.id,
        order: this.order,
        ok: true,
        capturedAt,
        facts: {
          count: turns.length,
          turns,
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
          unavailableReason: 'dialog_not_found_for_messages',
          facts: {},
        };
      }
      throw e;
    }
  }
}
