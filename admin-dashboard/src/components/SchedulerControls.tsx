import { useState } from "react";
import { Loader2, Play, Power } from "lucide-react";
import { runSchedulerNow, toggleSchedulerAutomation } from "@/api/retention";
import { getErrorMessage } from "@/api/client";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/hooks/use-toast";
import { labelJobStatus } from "@/i18n/ru";
import type { AutomationSettings } from "@/types/api";

interface SchedulerControlsProps {
  automation: AutomationSettings | null;
  loading?: boolean;
  onChanged: () => void;
}

export function SchedulerControls({
  automation,
  loading,
  onChanged,
}: SchedulerControlsProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggle = async () => {
    if (!automation) return;
    setBusy(true);
    setError(null);
    try {
      await toggleSchedulerAutomation(!automation.automation_enabled);
      toast({
        title: automation.automation_enabled
          ? "Автоматизация выключена"
          : "Автоматизация включена",
        variant: "success",
      });
      onChanged();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const runNow = async () => {
    setBusy(true);
    setError(null);
    try {
      await runSchedulerNow();
      toast({ title: "Задача удержания запущена", variant: "success" });
      onChanged();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Автоматизация retention</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">Загрузка…</CardContent>
      </Card>
    );
  }

  if (!automation) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Автоматизация retention</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Настройки автоматизации недоступны
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-2">
        <CardTitle>Автоматизация retention</CardTitle>
        <Badge variant={automation.automation_enabled ? "success" : "secondary"}>
          {automation.automation_enabled ? "Включена" : "Выключена"}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <Alert variant="destructive">{error}</Alert>}

        <div className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
          <p>Планировщик: {automation.scheduler_running ? "работает" : "остановлен"}</p>
          <p>Лимит в день: {automation.daily_send_limit}</p>
          <p>Размер пакета: {automation.send_pending_limit}</p>
          <p>
            Тихие часы (UTC): {automation.quiet_hours_start}:00 – {automation.quiet_hours_end}:00
          </p>
          <p>Тестовый режим: {automation.test_mode ? "вкл." : "выкл."}</p>
          <p>
            Последняя задача:{" "}
            {automation.last_job_status
              ? labelJobStatus(automation.last_job_status)
              : "—"}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => void toggle()} disabled={busy}>
            <Power className="h-4 w-4" />
            {automation.automation_enabled ? "Выключить" : "Включить"}
          </Button>
          <Button onClick={() => void runNow()} disabled={busy}>
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            Запустить сейчас
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
