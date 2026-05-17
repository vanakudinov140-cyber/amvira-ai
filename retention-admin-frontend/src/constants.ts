export const REFRESH_MS = 30_000;
export const MODERATION_FETCH_LIMIT = 200;
export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50] as const;

export const MODERATION_TABS = [
  { value: "pending", label: "На модерации" },
  { value: "approved", label: "Одобрено" },
  { value: "sent", label: "Отправлено" },
  { value: "rejected", label: "Отклонено" },
] as const;

export const ACTION_FILTER_OPTIONS = [
  { value: "all", label: "Все сценарии" },
  { value: "monthly_care", label: "Ежемесячный уход" },
  { value: "gentle_return", label: "Мягкое возвращение" },
  { value: "comeback_reminder", label: "Напоминание о визите" },
  { value: "winback", label: "Возврат клиента" },
] as const;

export const ENV_LABEL =
  import.meta.env.VITE_ENV_LABEL?.trim() || "Тестовый режим";
