export class TelegramWebhookSecretMismatchError extends Error {
  constructor() {
    super('Telegram webhook secret mismatch');
    this.name = 'TelegramWebhookSecretMismatchError';
  }
}

export class TelegramSendMessageError extends Error {
  constructor(
    message: string,
    public readonly httpStatus?: number,
    public readonly retryable?: boolean,
  ) {
    super(message);
    this.name = 'TelegramSendMessageError';
  }
}
