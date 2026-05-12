export type TelegramSendMessageResponse = {
  readonly ok: boolean;
  readonly description?: string;
  readonly error_code?: number;
  readonly parameters?: { retry_after?: number };
  readonly result?: { message_id?: number };
};
