import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Check,
  ChevronLeft,
  ChevronRight,
  Eye,
  Loader2,
  Pencil,
  Sparkles,
  X,
} from "lucide-react";
import {
  approveMessage,
  bulkApproveMessages,
  bulkRejectMessages,
  fetchModerationQueue,
  regenerateMessage,
  rejectMessage,
} from "@/api/retention";
import { getErrorMessage } from "@/api/client";
import { EmptyState } from "@/components/EmptyState";
import { ModerationAssistantDialog } from "@/components/ModerationAssistantDialog";
import { MessagePreviewDrawer } from "@/components/MessagePreviewDrawer";
import { MessageStatusBadge } from "@/components/MessageStatusBadge";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ACTION_FILTER_OPTIONS,
  DEFAULT_PAGE_SIZE,
  MODERATION_FETCH_LIMIT,
  MODERATION_TABS,
  PAGE_SIZE_OPTIONS,
} from "@/constants";
import { toast } from "@/hooks/use-toast";
import {
  defaultModerationFilters,
  filterMessages,
  paginateItems,
  canModerateStatus,
} from "@/lib/moderation";
import { labelAction, labelStatus } from "@/i18n/ru";
import { cn } from "@/lib/utils";
import type { MessageItem, MessageStatus } from "@/types/api";

interface ModerationSectionProps {
  refreshKey?: number;
}

export function ModerationSection({ refreshKey = 0 }: ModerationSectionProps) {
  const [tab, setTab] = useState<MessageStatus>("pending");
  const [items, setItems] = useState<MessageItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState(defaultModerationFilters);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [actionId, setActionId] = useState<number | null>(null);
  const [bulkBusy, setBulkBusy] = useState(false);
  const [preview, setPreview] = useState<MessageItem | null>(null);
  const [editor, setEditor] = useState<MessageItem | null>(null);

  const loadQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchModerationQueue({
        status: tab,
        limit: MODERATION_FETCH_LIMIT,
        offset: 0,
      });
      setItems(data.items);
      setTotal(data.total);
      setSelected(new Set());
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    void loadQueue();
  }, [loadQueue, refreshKey]);

  useEffect(() => {
    setPage(1);
    setSelected(new Set());
  }, [tab, filters.action, filters.clientIdSearch, filters.textSearch, pageSize]);

  const filtered = useMemo(
    () => filterMessages(items, filters),
    [items, filters],
  );

  const { items: pageItems, totalPages } = useMemo(
    () => paginateItems(filtered, page, pageSize),
    [filtered, page, pageSize],
  );

  const pendingTab = tab === "pending";
  const allPageSelected =
    pageItems.length > 0 && pageItems.every((i) => selected.has(i.id));

  const toggleSelectAll = () => {
    if (allPageSelected) {
      setSelected((prev) => {
        const next = new Set(prev);
        pageItems.forEach((i) => next.delete(i.id));
        return next;
      });
    } else {
      setSelected((prev) => {
        const next = new Set(prev);
        pageItems.forEach((i) => next.add(i.id));
        return next;
      });
    }
  };

  const runApprove = async (id: number) => {
    setActionId(id);
    try {
      await approveMessage(id);
      toast({ title: "Одобрено", description: `Сообщение #${id}`, variant: "success" });
      setPreview((p) => (p?.id === id ? null : p));
      await loadQueue();
    } catch (err) {
      toast({
        title: "Ошибка одобрения",
        description: getErrorMessage(err),
        variant: "destructive",
      });
    } finally {
      setActionId(null);
    }
  };

  const runRegenerate = async (id: number) => {
    setActionId(id);
    try {
      await regenerateMessage(id);
      toast({
        title: "Текст перегенерирован",
        description: `Сообщение #${id}`,
        variant: "success",
      });
      await loadQueue();
    } catch (err) {
      toast({
        title: "Ошибка перегенерации",
        description: getErrorMessage(err),
        variant: "destructive",
      });
    } finally {
      setActionId(null);
    }
  };

  const runReject = async (id: number) => {
    setActionId(id);
    try {
      await rejectMessage(id);
      toast({ title: "Отклонено", description: `Сообщение #${id}`, variant: "default" });
      setPreview((p) => (p?.id === id ? null : p));
      await loadQueue();
    } catch (err) {
      toast({
        title: "Ошибка отклонения",
        description: getErrorMessage(err),
        variant: "destructive",
      });
    } finally {
      setActionId(null);
    }
  };

  const runBulk = async (action: "approve" | "reject") => {
    const ids = [...selected];
    if (!ids.length) return;
    setBulkBusy(true);
    try {
      if (action === "approve") await bulkApproveMessages(ids);
      else await bulkRejectMessages(ids);
      toast({
        title: action === "approve" ? "Массовое одобрение" : "Массовое отклонение",
        description: `${ids.length} сообщений`,
        variant: action === "approve" ? "success" : "default",
      });
      await loadQueue();
    } catch (err) {
      toast({
        title: "Ошибка массовой операции",
        description: getErrorMessage(err),
        variant: "destructive",
      });
    } finally {
      setBulkBusy(false);
    }
  };

  return (
    <>
      <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle>Модерация сообщений</CardTitle>
            <p className="text-xs text-muted-foreground">
              Всего в API: {total} · после фильтров: {filtered.length}
            </p>
          </div>

          <div className="flex flex-wrap gap-1">
            {MODERATION_TABS.map((t) => (
              <Button
                key={t.value}
                size="sm"
                variant={tab === t.value ? "default" : "outline"}
                onClick={() => setTab(t.value)}
              >
                {t.label}
              </Button>
            ))}
          </div>

          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            <select
              className="h-9 rounded-md border border-border bg-background px-3 text-sm"
              value={filters.action}
              onChange={(e) =>
                setFilters((f) => ({ ...f, action: e.target.value }))
              }
            >
              {ACTION_FILTER_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            <Input
              placeholder="ID клиента"
              value={filters.clientIdSearch}
              onChange={(e) =>
                setFilters((f) => ({ ...f, clientIdSearch: e.target.value }))
              }
            />
            <Input
              className="sm:col-span-2"
              placeholder="Поиск по тексту"
              value={filters.textSearch}
              onChange={(e) =>
                setFilters((f) => ({ ...f, textSearch: e.target.value }))
              }
            />
          </div>

          {pendingTab && selected.size > 0 && (
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="success"
                disabled={bulkBusy}
                onClick={() => void runBulk("approve")}
              >
                {bulkBusy ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Check className="h-4 w-4" />
                )}
                Одобрить ({selected.size})
              </Button>
              <Button
                size="sm"
                variant="destructive"
                disabled={bulkBusy}
                onClick={() => void runBulk("reject")}
              >
                <X className="h-4 w-4" />
                Отклонить ({selected.size})
              </Button>
            </div>
          )}
        </CardHeader>

        <CardContent className="space-y-3">
          {error && <Alert variant="destructive">{error}</Alert>}

          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : pageItems.length === 0 ? (
            <EmptyState
              title="Нет сообщений"
              description={`Вкладка «${labelStatus(tab)}» пуста или фильтры ничего не нашли`}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="border-b border-border text-muted-foreground">
                  <tr>
                    {pendingTab && (
                      <th className="w-10 px-2 py-2">
                        <input
                          type="checkbox"
                          checked={allPageSelected}
                          onChange={toggleSelectAll}
                          aria-label="Выбрать все на странице"
                        />
                      </th>
                    )}
                    <th className="px-2 py-2">ID</th>
                    <th className="px-2 py-2">Клиент</th>
                    <th className="px-2 py-2">Сценарий</th>
                    <th className="px-2 py-2">Текст</th>
                    <th className="px-2 py-2">Статус</th>
                    <th className="px-2 py-2 text-right">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {pageItems.map((item) => {
                    const busy = actionId === item.id || bulkBusy;
                    const checked = selected.has(item.id);
                    return (
                      <tr
                        key={item.id}
                        className={cn(
                          "border-b border-border/60 align-top transition-colors",
                          checked && "bg-primary/5",
                        )}
                      >
                        {pendingTab && (
                          <td className="px-2 py-3">
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() =>
                                setSelected((prev) => {
                                  const next = new Set(prev);
                                  if (next.has(item.id)) next.delete(item.id);
                                  else next.add(item.id);
                                  return next;
                                })
                              }
                            />
                          </td>
                        )}
                        <td className="px-2 py-3 tabular-nums text-muted-foreground">
                          {item.id}
                        </td>
                        <td className="px-2 py-3 tabular-nums">{item.client_id}</td>
                        <td className="px-2 py-3">
                          <Badge variant="outline">{labelAction(item.action)}</Badge>
                        </td>
                        <td className="max-w-xs px-2 py-3">
                          <button
                            type="button"
                            className="line-clamp-2 text-left hover:text-primary"
                            onClick={() => setPreview(item)}
                          >
                            {item.text}
                          </button>
                        </td>
                        <td className="px-2 py-3">
                          <MessageStatusBadge status={item.status} />
                        </td>
                        <td className="px-2 py-3">
                          <div className="flex justify-end gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => setPreview(item)}
                              disabled={busy}
                            >
                              <Eye className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              title="Редактировать"
                              onClick={() => setEditor(item)}
                              disabled={busy}
                            >
                              <Pencil className="h-3.5 w-3.5" />
                            </Button>
                            {(item.status === "pending" || item.status === "approved") && (
                              <Button
                                size="sm"
                                variant="secondary"
                                title="Перегенерировать AI"
                                onClick={() => void runRegenerate(item.id)}
                                disabled={busy}
                              >
                                <Sparkles className="h-3.5 w-3.5" />
                              </Button>
                            )}
                            {canModerateStatus(item.status) && (
                              <>
                                <Button
                                  size="sm"
                                  variant="success"
                                  onClick={() => void runApprove(item.id)}
                                  disabled={busy}
                                >
                                  <Check className="h-3.5 w-3.5" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => void runReject(item.id)}
                                  disabled={busy}
                                >
                                  <X className="h-3.5 w-3.5" />
                                </Button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {!loading && filtered.length > 0 && (
            <div className="flex flex-col gap-3 border-t border-border pt-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>Стр. {page} / {totalPages}</span>
                <select
                  className="h-8 rounded-md border border-border bg-background px-2 text-xs"
                  value={pageSize}
                  onChange={(e) => setPageSize(Number(e.target.value))}
                >
                  {PAGE_SIZE_OPTIONS.map((n) => (
                    <option key={n} value={n}>
                      {n} на странице
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <MessagePreviewDrawer
        message={preview}
        open={preview !== null}
        busy={actionId !== null}
        onClose={() => setPreview(null)}
        onEdit={(m) => {
          setPreview(null);
          setEditor(m);
        }}
        onRegenerate={(id) => void runRegenerate(id)}
        onApprove={(id) => void runApprove(id)}
        onReject={(id) => void runReject(id)}
      />

      <ModerationAssistantDialog
        message={editor}
        open={editor !== null}
        onClose={() => setEditor(null)}
        onUpdated={(m) => {
          setEditor(m);
          void loadQueue();
        }}
        onApproved={() => {
          toast({ title: "Одобрено", variant: "success" });
          setEditor(null);
          void loadQueue();
        }}
        onRejected={() => {
          toast({ title: "Отклонено", variant: "default" });
          setEditor(null);
          void loadQueue();
        }}
      />
    </>
  );
}
