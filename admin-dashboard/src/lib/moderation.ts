import type { MessageItem, MessageStatus } from "@/types/api";

export interface ModerationFilters {
  action: string;
  clientIdSearch: string;
  textSearch: string;
}

export const defaultModerationFilters = (): ModerationFilters => ({
  action: "all",
  clientIdSearch: "",
  textSearch: "",
});

export function filterMessages(
  items: MessageItem[],
  filters: ModerationFilters,
): MessageItem[] {
  return items.filter((item) => {
    if (filters.action !== "all" && item.action !== filters.action) {
      return false;
    }
    if (filters.clientIdSearch.trim()) {
      const q = filters.clientIdSearch.trim();
      if (!String(item.client_id).includes(q)) return false;
    }
    if (filters.textSearch.trim()) {
      const q = filters.textSearch.trim().toLowerCase();
      if (!item.text.toLowerCase().includes(q)) return false;
    }
    return true;
  });
}

export function paginateItems<T>(
  items: T[],
  page: number,
  pageSize: number,
): { items: T[]; totalPages: number; total: number } {
  const total = items.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const start = (safePage - 1) * pageSize;
  return {
    items: items.slice(start, start + pageSize),
    totalPages,
    total,
  };
}

export function canModerateStatus(status: MessageStatus): boolean {
  return status === "pending";
}
