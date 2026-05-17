import { useCallback, useState } from "react";
import { Loader2, Send } from "lucide-react";
import { sendApprovedMessages } from "@/api/retention";
import { getErrorMessage } from "@/api/client";
import { AnalyticsCards } from "@/components/AnalyticsCards";
import { AnalyticsCharts } from "@/components/AnalyticsCharts";
import { DashboardHeader } from "@/components/DashboardHeader";
import { AiPerformanceSection } from "@/components/AiPerformanceSection";
import { ModerationInsightsCharts } from "@/components/ModerationInsightsCharts";
import { ModerationSection } from "@/components/ModerationSection";
import { SchedulerControls } from "@/components/SchedulerControls";
import { SchedulerStatus } from "@/components/SchedulerStatus";
import { TestModeBanner } from "@/components/TestModeBanner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAutoRefresh } from "@/hooks/useAutoRefresh";
import { toast } from "@/hooks/use-toast";
import { useRetentionAnalytics } from "@/hooks/useRetentionAnalytics";

export function Dashboard() {
  const { overview, scheduler, automation, insights, aiPerformance, loading, load } =
    useRetentionAnalytics();
  const [moderationKey, setModerationKey] = useState(0);
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState<{ sent: number; failed: number } | null>(
    null,
  );

  const refreshAll = useCallback(async () => {
    await load();
    setModerationKey((k) => k + 1);
  }, [load]);

  const { refreshing, lastRefreshedAt, refresh } = useAutoRefresh(refreshAll);

  const handleSend = async () => {
    setSending(true);
    setSendResult(null);
    try {
      const result = await sendApprovedMessages();
      setSendResult(result);
      toast({
        title: "Отправка завершена",
        description: `отправлено: ${result.sent}, ошибок: ${result.failed}`,
        variant: result.failed > 0 ? "destructive" : "success",
      });
      await refresh(true);
    } catch (err) {
      toast({
        title: "Ошибка отправки",
        description: getErrorMessage(err),
        variant: "destructive",
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <TestModeBanner automation={automation} />
      <DashboardHeader
        refreshing={refreshing || loading}
        lastRefreshedAt={lastRefreshedAt}
        onRefresh={() => void refresh(false)}
      />

      <main className="mx-auto max-w-7xl space-y-8 px-4 py-6">
        <section className="space-y-4">
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
            Аналитика
          </h2>
          <AnalyticsCards overview={overview} loading={loading} />
          <AnalyticsCharts overview={overview} loading={loading} />
          <ModerationInsightsCharts insights={insights} loading={loading} />
          <AiPerformanceSection performance={aiPerformance} loading={loading} />
          <div className="grid gap-4 lg:grid-cols-2">
            <SchedulerStatus status={scheduler} loading={loading} />
            <SchedulerControls
              automation={automation}
              loading={loading}
              onChanged={() => void refresh(true)}
            />
          </div>
        </section>

        <section className="space-y-3">
          <Card>
            <CardHeader>
              <CardTitle>Ручная отправка</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-muted-foreground">
                Отправляет только <strong>одобренные</strong> сообщения (тестовый режим и
                ограничения на сервере).
              </p>
              <Button onClick={() => void handleSend()} disabled={sending || loading}>
                {sending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                Отправить одобренные
              </Button>
            </CardContent>
            {sendResult && (
              <CardContent className="border-t border-border pt-0">
                <p className="text-sm">
                  Результат:{" "}
                  <span className="text-green-300">отправлено: {sendResult.sent}</span>
                  {" · "}
                  <span className="text-red-300">ошибок: {sendResult.failed}</span>
                </p>
              </CardContent>
            )}
          </Card>
        </section>

        <section className="space-y-3">
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
            Модерация
          </h2>
          <ModerationSection refreshKey={moderationKey} />
        </section>
      </main>
    </div>
  );
}
