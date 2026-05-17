import { useCallback, useEffect, useMemo, useState } from "react";
import { Check, Loader2, RefreshCw, X } from "lucide-react";
import {
  approveMessage,
  fetchPendingMessages,
  fetchRetentionCandidates,
  rejectMessage,
} from "@/api/retention";
import { getErrorMessage } from "@/api/client";
import { EmptyState } from "@/components/EmptyState";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/hooks/use-toast";
import { labelAction } from "@/i18n/ru";
import type { MessageItem } from "@/types/api";

export function PendingMessagesPage() {
  const [items, setItems] = useState<MessageItem[]>([]);
  const [clientNames, setClientNames] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionId, setActionId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [pending, candidates] = await Promise.all([
        fetchPendingMessages(),
        fetchRetentionCandidates().catch(() => ({ count: 0, items: [] })),
      ]);
      setItems(pending.items);
      const map: Record<number, string> = {};
      for (const c of candidates.items) {
        map[c.client_id] = c.client_name;
      }
      setClientNames(map);
    } catch (err) {
      const msg = getErrorMessage(err);
      setError(msg);
      toast({ title: "Ошибка загрузки", description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const clientLabel = useMemo(
    () => (clientId: number) => clientNames[clientId] ?? `Клиент #${clientId}`,
    [clientNames],
  );

  const handleApprove = async (id: number) => {
    setActionId(id);
    try {
      await approveMessage(id);
      setItems((prev) => prev.filter((m) => m.id !== id));
      toast({ title: "Одобрено", variant: "success" });
    } catch (err) {
      toast({
        title: "Ошибка",
        description: getErrorMessage(err),
        variant: "destructive",
      });
    } finally {
      setActionId(null);
    }
  };

  const handleReject = async (id: number) => {
    setActionId(id);
    try {
      await rejectMessage(id);
      setItems((prev) => prev.filter((m) => m.id !== id));
      toast({ title: "Отклонено", variant: "success" });
    } catch (err) {
      toast({
        title: "Ошибка",
        description: getErrorMessage(err),
        variant: "destructive",
      });
    } finally {
      setActionId(null);
    }
  };

  return (
    <main className="mx-auto max-w-7xl space-y-4 px-4 py-6">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">Pending Messages</h2>
        <Button variant="secondary" onClick={() => void load()} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Обновить
        </Button>
      </div>

      {error && <Alert variant="destructive">{error}</Alert>}

      <Card>
        <CardHeader>
          <CardTitle>На модерации ({items.length})</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          {loading ? (
            <Skeleton className="h-48 w-full" />
          ) : items.length === 0 ? (
            <EmptyState title="Нет pending сообщений" description="Подготовьте сообщения через retention pipeline." />
          ) : (
            <table className="w-full min-w-[900px] text-left text-sm">
              <thead className="border-b border-border text-muted-foreground">
                <tr>
                  <th className="py-2 pr-4">Client</th>
                  <th className="py-2 pr-4">Text</th>
                  <th className="py-2 pr-4">Action</th>
                  <th className="py-2">Approve / Reject</th>
                </tr>
              </thead>
              <tbody>
                {items.map((msg) => {
                  const busy = actionId === msg.id;
                  return (
                    <tr key={msg.id} className="border-b border-border/60 align-top">
                      <td className="py-3 pr-4 font-medium whitespace-nowrap">
                        {clientLabel(msg.client_id)}
                      </td>
                      <td className="py-3 pr-4 max-w-md">
                        <p className="line-clamp-3 text-muted-foreground">{msg.text}</p>
                      </td>
                      <td className="py-3 pr-4 whitespace-nowrap">
                        {labelAction(msg.action)}
                      </td>
                      <td className="py-3">
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => void handleApprove(msg.id)}
                            disabled={busy}
                          >
                            {busy ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Check className="h-4 w-4" />
                            )}
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => void handleReject(msg.id)}
                            disabled={busy}
                          >
                            <X className="h-4 w-4" />
                            Reject
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
