import { Clock, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { labelJobStatus } from "@/i18n/ru";
import { formatDateTime } from "@/lib/utils";
import type { SchedulerStatus as SchedulerStatusType } from "@/types/api";

interface SchedulerStatusProps {
  status: SchedulerStatusType | null;
  loading?: boolean;
}

export function SchedulerStatus({ status, loading }: SchedulerStatusProps) {
  const running = status?.scheduler_running ?? false;
  const jobStatus = status?.last_job_status;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Планировщик
        </CardTitle>
        <RefreshCw
          className={`h-4 w-4 text-muted-foreground ${loading ? "animate-spin" : ""}`}
        />
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-muted-foreground">Статус:</span>
          <Badge variant={running ? "success" : "secondary"}>
            {loading ? "…" : running ? "работает" : "остановлен"}
          </Badge>
          {jobStatus && (
            <Badge
              variant={
                jobStatus === "success"
                  ? "success"
                  : jobStatus === "failed"
                    ? "destructive"
                    : "outline"
              }
            >
              задача: {labelJobStatus(jobStatus)}
            </Badge>
          )}
        </div>
        <div className="grid gap-1 text-muted-foreground sm:grid-cols-2">
          <p>Старт: {formatDateTime(status?.last_job_started_at)}</p>
          <p>Финиш: {formatDateTime(status?.last_job_finished_at)}</p>
        </div>
        {status?.last_job_error && (
          <p className="rounded-md border border-destructive/40 bg-destructive/10 p-2 text-red-200">
            {status.last_job_error}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
