import type { MessageStatus } from "@/types/api";

export const MESSAGE_STATUS_LABELS: Record<MessageStatus, string> = {
  pending: "На модерации",
  approved: "Одобрено",
  rejected: "Отклонено",
  sent: "Отправлено",
  failed: "Ошибка отправки",
};

export const ACTION_LABELS: Record<string, string> = {
  monthly_care: "Ежемесячный уход",
  gentle_return: "Мягкое возвращение",
  comeback_reminder: "Напоминание о визите",
  winback: "Возврат клиента",
};

export const SEGMENT_LABELS: Record<string, string> = {
  new: "Новый клиент",
  active: "Активный",
  loyal: "Лояльный",
  sleeping: "Спящий",
  lost_vip: "VIP без визитов",
  regular: "Постоянные",
  at_risk: "Под риском",
  dormant: "Спящие",
  churned: "Ушедшие",
  vip: "VIP",
  unknown: "Не определён",
};

export const VERSION_SOURCE_LABELS: Record<string, string> = {
  ai: "AI",
  edit: "Редактирование",
  regenerate: "Перегенерация",
  manual: "Вручную",
};

export const JOB_STATUS_LABELS: Record<string, string> = {
  success: "Успешно",
  failed: "Ошибка",
  running: "Выполняется",
  idle: "Ожидание",
};

export function labelStatus(status: MessageStatus | string): string {
  return MESSAGE_STATUS_LABELS[status as MessageStatus] ?? status;
}

export function labelAction(action: string): string {
  return ACTION_LABELS[action] ?? action;
}

export function labelSegment(segment: string): string {
  return SEGMENT_LABELS[segment] ?? segment;
}

export function labelVersionSource(source: string): string {
  return VERSION_SOURCE_LABELS[source] ?? source;
}

export function labelJobStatus(status: string): string {
  return JOB_STATUS_LABELS[status] ?? status;
}

const CHANNEL_LABELS: Record<string, string> = {
  whatsapp: "WhatsApp",
  sms: "SMS",
  telegram: "Telegram",
};

export function labelChannel(channel: string): string {
  return CHANNEL_LABELS[channel] ?? channel;
}

const TRIGGER_LABELS: Record<string, string> = {
  regular_care: "Пора поддерживающего ухода",
  moderate_absence: "Заметная пауза между визитами",
  long_absence: "Длительное отсутствие",
};

export function labelTriggerReason(trigger: string): string {
  return TRIGGER_LABELS[trigger] ?? trigger;
}
