import { RefreshCw } from "lucide-react";
import { ENV_LABEL, REFRESH_MS } from "@/constants";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface DashboardHeaderProps {
  refreshing: boolean;
  lastRefreshedAt: Date | null;
  onRefresh: () => void;
}

export function DashboardHeader({
  refreshing,
  lastRefreshedAt,
  onRefresh,
}: DashboardHeaderProps) {
  return (
    <header className="border-b border-border bg-card/60 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">CRM удержания клиентов</h1>
            <Badge variant="outline" className="border-amber-500/50 text-amber-200">
              {ENV_LABEL}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Модерация retention-сообщений · демо-панель для салона
          </p>
          <p className="text-xs text-muted-foreground">
            Автообновление каждые {REFRESH_MS / 1000} с
            {lastRefreshedAt &&
              ` · обновлено ${lastRefreshedAt.toLocaleTimeString("ru-RU")}`}
          </p>
        </div>
        <Button variant="secondary" onClick={onRefresh} disabled={refreshing}>
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
          Обновить сейчас
        </Button>
      </div>
    </header>
  );
}
