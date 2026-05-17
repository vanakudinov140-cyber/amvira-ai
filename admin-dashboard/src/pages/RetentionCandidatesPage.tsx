import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { fetchRetentionCandidates } from "@/api/retention";
import { getErrorMessage } from "@/api/client";
import { EmptyState } from "@/components/EmptyState";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/hooks/use-toast";
import { labelAction } from "@/i18n/ru";
import type { RetentionCandidate } from "@/types/api";

export function RetentionCandidatesPage() {
  const [items, setItems] = useState<RetentionCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRetentionCandidates();
      setItems(data.items);
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

  return (
    <main className="mx-auto max-w-7xl space-y-4 px-4 py-6">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">Retention Candidates</h2>
        <Button variant="secondary" onClick={() => void load()} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Обновить
        </Button>
      </div>

      {error && <Alert variant="destructive">{error}</Alert>}

      <Card>
        <CardHeader>
          <CardTitle>Кандидаты на удержание ({items.length})</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          {loading ? (
            <Skeleton className="h-48 w-full" />
          ) : items.length === 0 ? (
            <EmptyState title="Нет кандидатов" description="Запустите sync visits и подготовку сообщений." />
          ) : (
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b border-border text-muted-foreground">
                <tr>
                  <th className="py-2 pr-4">Клиент</th>
                  <th className="py-2 pr-4">Процедура</th>
                  <th className="py-2 pr-4">Последний визит</th>
                  <th className="py-2 pr-4">Дней</th>
                  <th className="py-2 pr-4">Действие</th>
                  <th className="py-2">Канал</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.client_id} className="border-b border-border/60">
                    <td className="py-3 pr-4 font-medium">{row.client_name}</td>
                    <td className="py-3 pr-4">{row.procedure_name}</td>
                    <td className="py-3 pr-4">{row.last_visit_date}</td>
                    <td className="py-3 pr-4">{row.days_since_visit}</td>
                    <td className="py-3 pr-4">{labelAction(row.recommended_action)}</td>
                    <td className="py-3">{row.recommended_channel}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
