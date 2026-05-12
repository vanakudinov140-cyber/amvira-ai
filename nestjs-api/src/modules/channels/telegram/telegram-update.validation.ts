import type { TelegramUpdate } from './telegram.types';

export function isTelegramUpdatePayload(value: unknown): value is TelegramUpdate {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const u = value as Record<string, unknown>;
  return typeof u.update_id === 'number';
}

export function isTelegramTextMessageUpdate(value: unknown): value is TelegramUpdate {
  if (!isTelegramUpdatePayload(value)) {
    return false;
  }
  const msg = value.message;
  if (!msg || typeof msg !== 'object') {
    return false;
  }
  const m = msg as Record<string, unknown>;
  const chat = m.chat;
  if (!chat || typeof chat !== 'object') {
    return false;
  }
  const c = chat as Record<string, unknown>;
  return typeof c.id === 'number' && typeof m.text === 'string' && m.text.length > 0;
}
