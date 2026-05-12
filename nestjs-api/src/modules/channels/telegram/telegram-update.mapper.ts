import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import type { UserMessageOrchestrationRequest } from '../../conversations/contracts/user-message-orchestration.request';
import type { TelegramUpdate } from './telegram.types';
import { TELEGRAM_CHAT_ID_METADATA_KEY } from './contracts/telegram-metadata.contract';

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

@Injectable()
export class TelegramUpdateMapper {
  constructor(private readonly config: ConfigService) {}

  toOrchestrationRequest(
    update: TelegramUpdate,
  ): UserMessageOrchestrationRequest | null {
    const msg = update.message;
    if (!msg?.text || !msg.chat) {
      return null;
    }

    let dialogId = this.parseDialogIdFromStart(msg.text);
    if (!dialogId) {
      dialogId =
        this.config.get<string>('telegram.mvpDefaultDialogId')?.trim() ?? '';
    }
    if (!dialogId || !UUID_RE.test(dialogId)) {
      return null;
    }

    const correlationId = `tg:update:${update.update_id}`;
    const turnIdempotencyKey = `tg:update:${update.update_id}`;

    return {
      dialogId,
      userText: msg.text,
      correlationId,
      turnIdempotencyKey,
      persistAssistantMessage: true,
      dispatchToChannel: true,
      deferChannelDispatch: false,
      channelMetadata: {
        [TELEGRAM_CHAT_ID_METADATA_KEY]: msg.chat.id,
      },
    };
  }

  private parseDialogIdFromStart(text: string): string | undefined {
    const m = text.match(/^\/start\s+([^\s]+)/);
    if (!m) {
      return undefined;
    }
    const candidate = m[1];
    return UUID_RE.test(candidate) ? candidate : undefined;
  }
}
