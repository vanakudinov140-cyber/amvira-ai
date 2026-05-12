import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

type TelegramApiResponse = {
  ok?: boolean;
  description?: string;
};

/**
 * Calls Telegram Bot HTTP API for webhook lifecycle (no SDK).
 */
@Injectable()
export class TelegramWebhookBootstrapService implements OnModuleInit {
  private readonly logger = new Logger(TelegramWebhookBootstrapService.name);

  constructor(private readonly config: ConfigService) {}

  async onModuleInit(): Promise<void> {
    const sync = this.config.get<boolean>('telegram.webhookSyncOnStartup');
    if (!sync) {
      return;
    }
    const url = this.config.get<string>('telegram.webhookUrl')?.trim();
    const token = this.config.get<string>('telegram.botToken')?.trim();
    const secret = this.config.get<string>('telegram.webhookSecretToken')?.trim();
    if (!url || !token) {
      this.logger.warn(
        'TELEGRAM_WEBHOOK_SYNC_ON_STARTUP is true but TELEGRAM_WEBHOOK_URL or TELEGRAM_BOT_TOKEN is missing — skipping setWebhook',
      );
      return;
    }
    await this.setWebhook(token, url, secret);
  }

  async setWebhook(
    token: string,
    url: string,
    secretToken?: string,
  ): Promise<TelegramApiResponse> {
    const body: Record<string, unknown> = { url };
    if (secretToken) {
      body.secret_token = secretToken;
    }
    const res = await fetch(
      `https://api.telegram.org/bot${token}/setWebhook`,
      {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      },
    );
    const json = (await res.json()) as TelegramApiResponse;
    if (!json.ok) {
      this.logger.error(
        `setWebhook failed: ${json.description ?? res.statusText}`,
      );
    } else {
      this.logger.log(`setWebhook ok for url=${url}`);
    }
    return json;
  }

  async removeWebhook(token: string): Promise<TelegramApiResponse> {
    const res = await fetch(
      `https://api.telegram.org/bot${token}/deleteWebhook`,
      {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ drop_pending_updates: false }),
      },
    );
    const json = (await res.json()) as TelegramApiResponse;
    if (!json.ok) {
      this.logger.error(
        `deleteWebhook failed: ${json.description ?? res.statusText}`,
      );
    } else {
      this.logger.log('deleteWebhook ok');
    }
    return json;
  }
}
