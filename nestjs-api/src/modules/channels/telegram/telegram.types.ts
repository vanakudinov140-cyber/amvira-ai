/**
 * Minimal Telegram Bot API shapes for MVP (text messages only).
 */
export type TelegramChat = {
  readonly id: number;
};

export type TelegramMessage = {
  readonly message_id: number;
  readonly chat: TelegramChat;
  readonly text?: string;
};

export type TelegramUpdate = {
  readonly update_id: number;
  readonly message?: TelegramMessage;
};
