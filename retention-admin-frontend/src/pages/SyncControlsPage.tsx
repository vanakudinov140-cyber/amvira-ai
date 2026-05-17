import { useState } from "react";
import { Loader2, Play, Users, Calendar } from "lucide-react";
import { runSchedulerNow, syncClients, syncVisits } from "@/api/retention";
import { getErrorMessage } from "@/api/client";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/hooks/use-toast";

type Job = "clients" | "visits" | "scheduler" | null;

export function SyncControlsPage() {
  const [busy, setBusy] = useState<Job>(null);
  const [lastResult, setLastResult] = useState<string | null>(null);

  const run = async (job: Job, fn: () => Promise<{ synced?: number } | void>) => {
    if (!job) return;
    setBusy(job);
    setLastResult(null);
    try {
      const result = await fn();
      const synced = result && "synced" in result ? result.synced : undefined;
      const text =
        synced !== undefined
          ? `${job}: синхронизировано ${synced}`
          : `${job}: выполнено`;
      setLastResult(text);
      toast({ title: "Готово", description: text, variant: "success" });
    } catch (err) {
      const msg = getErrorMessage(err);
      setLastResult(msg);
      toast({ title: "Ошибка", description: msg, variant: "destructive" });
    } finally {
      setBusy(null);
    }
  };

  return (
    <main className="mx-auto max-w-7xl space-y-4 px-4 py-6">
      <h2 className="text-lg font-semibold">Sync Controls</h2>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Users className="h-5 w-5" />
              Sync Clients
            </CardTitle>
            <p className="text-sm text-muted-foreground">Загрузка клиентов из YCLIENTS</p>
          </CardHeader>
          <CardContent>
            <Button
              className="w-full"
              onClick={() => void run("clients", syncClients)}
              disabled={busy !== null}
            >
              {busy === "clients" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Users className="h-4 w-4" />
              )}
              Sync Clients
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Calendar className="h-5 w-5" />
              Sync Visits
            </CardTitle>
            <p className="text-sm text-muted-foreground">Загрузка визитов из YCLIENTS</p>
          </CardHeader>
          <CardContent>
            <Button
              className="w-full"
              onClick={() => void run("visits", syncVisits)}
              disabled={busy !== null}
            >
              {busy === "visits" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Calendar className="h-4 w-4" />
              )}
              Sync Visits
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Play className="h-5 w-5" />
              Run Scheduler
            </CardTitle>
            <p className="text-sm text-muted-foreground">Ручной запуск retention pipeline</p>
          </CardHeader>
          <CardContent>
            <Button
              className="w-full"
              variant="secondary"
              onClick={() => void run("scheduler", runSchedulerNow)}
              disabled={busy !== null}
            >
              {busy === "scheduler" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              Run Scheduler
            </Button>
          </CardContent>
        </Card>
      </div>

      {lastResult && (
        <Alert variant={lastResult.includes("Ошибка") ? "destructive" : "default"}>
          {lastResult}
        </Alert>
      )}
    </main>
  );
}
