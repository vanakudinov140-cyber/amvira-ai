import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import type { ChannelAdapter } from '../channel-adapter.contract';
import type { ChannelOutboundMessage } from '../channel-outbound-message.contract';
import type { DeliveryReceipt } from '../../../shared/integrations/delivery-receipt.contract';
import type { TelegramSendMessageResponse } from './contracts/telegram-send-message-response.contract';
import { TELEGRAM_CHAT_ID_METADATA_KEY } from './contracts/telegram-metadata.contract';
import { TelegramSendMessageError } from './telegram.errors';

const SEND_TIMEOUT_MS = 10_000;
const MAX_ATTEMPTS = 2;

@Injectable()
export class TelegramChannelAdapter implements ChannelAdapter {
  readonly channelKey = 'telegram';
  readonly capabilities = {
    maxBodyLength: 4096,
    supportsRichText: false,
    supportsButtons: false,
  } as const;

  private readonly logger = new Logger(TelegramChannelAdapter.name);

  constructor(private readonly config: ConfigService) {}

  async deliver(message: ChannelOutboundMessage): Promise<DeliveryReceipt> {
    const token = this.config.get<string>('telegram.botToken')?.trim();
    const now = new Date();
    if (!token) {
      this.logDelivery('missing_token', message);
      return {
        idempotencyKey: message.idempotencyKey,
        deliveredAt: now,
        channelKey: this.channelKey,
        status: 'failed',
        detail: 'telegram_bot_token_missing',
      };
    }

    const rawChatId = message.metadata?.[TELEGRAM_CHAT_ID_METADATA_KEY];
    const chatId =
      typeof rawChatId === 'number'
        ? rawChatId
        : typeof rawChatId === 'string'
          ? Number(rawChatId)
          : NaN;
    if (!Number.isFinite(chatId)) {
      this.logDelivery('missing_chat_id', message);
      return {
        idempotencyKey: message.idempotencyKey,
        deliveredAt: now,
        channelKey: this.channelKey,
        status: 'failed',
        detail: 'telegram_chat_id_missing',
      };
    }

    try {
      await this.sendMessageWithRetries(token, chatId, message.body);
      this.logDelivery('ok', message, { chatId });
      return {
        idempotencyKey: message.idempotencyKey,
        deliveredAt: new Date(),
        channelKey: this.channelKey,
        status: 'ack',
      };
    } catch (e) {
      const detail =
        e instanceof TelegramSendMessageError
          ? e.message
          : e instanceof Error
            ? e.message
            : String(e);
      this.logDelivery('failed', message, { chatId, detail });
      return {
        idempotencyKey: message.idempotencyKey,
        deliveredAt: new Date(),
        channelKey: this.channelKey,
        status: 'failed',
        detail,
      };
    }
  }

  private logDelivery(
    outcome: string,
    message: ChannelOutboundMessage,
    extra?: Record<string, unknown>,
  ): void {
    this.logger.log(
      JSON.stringify({
        scope: 'telegram.deliver',
        outcome,
        idempotencyKey: message.idempotencyKey,
        correlationId: message.correlation?.correlationId,
        ...extra,
      }),
    );
  }

  private async sendMessageWithRetries(
    token: string,
    chatId: number,
    text: string,
  ): Promise<void> {
    let lastErr: unknown;
    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
      try {
        await this.sendMessageOnce(token, chatId, text);
        return;
      } catch (e) {
        lastErr = e;
        const retryable =
          e instanceof TelegramSendMessageError && e.retryable === true;
        if (!retryable || attempt === MAX_ATTEMPTS) {
          throw e;
        }
        const backoff = e instanceof TelegramSendMessageError ? 200 : 200;
        await new Promise((r) => setTimeout(r, backoff));
      }
    }
    throw lastErr;
  }

  private async sendMessageOnce(
    token: string,
    chatId: number,
    text: string,
  ): Promise<void> {
    const url = `https://api.telegram.org/bot${token}/sendMessage`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), SEND_TIMEOUT_MS);
    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          chat_id: chatId,
          text,
          disable_web_page_preview: true,
        }),
        signal: controller.signal,
      });
    } catch (e) {
      const isAbort = e instanceof Error && e.name === 'AbortError';
      throw new TelegramSendMessageError(
        isAbort ? 'telegram_send_timeout' : 'telegram_send_network',
        undefined,
        true,
      );
    } finally {
      clearTimeout(timer);
    }

    const json = (await response.json()) as TelegramSendMessageResponse;
    if (!response.ok) {
      const retryable = this.isRetryableHttp(response.status);
      throw new TelegramSendMessageError(
        json.description ?? `http_${response.status}`,
        response.status,
        retryable,
      );
    }
    if (!json.ok) {
      const retryable =
        json.error_code === 429 ||
        (typeof json.error_code === 'number' && json.error_code >= 500);
      throw new TelegramSendMessageError(
        json.description ?? 'telegram_api_error',
        json.error_code,
        retryable,
      );
    }
  }

  private isRetryableHttp(status: number): boolean {
    return status === 429 || status >= 500;
  }
}
