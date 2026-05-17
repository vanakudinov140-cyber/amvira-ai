import { Users, MessageSquare, CheckCircle2, Send } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { RetentionOverview } from "@/types/api";

interface AnalyticsCardsProps {
  overview: RetentionOverview | null;
  loading?: boolean;
}

const items = [
  { key: "clients_total", label: "Клиенты", icon: Users },
  { key: "retention_candidates", label: "Кандидаты на возврат", icon: Users },
  { key: "messages_pending", label: "На модерации", icon: MessageSquare },
  { key: "messages_approved", label: "Одобрено", icon: CheckCircle2 },
  { key: "messages_sent", label: "Отправлено", icon: Send },
] as const;

export function AnalyticsCards({ overview, loading }: AnalyticsCardsProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      {items.map(({ key, label, icon: Icon }) => (
        <Card key={key}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-xs text-muted-foreground">{label}</CardTitle>
            <Icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <p className="text-2xl font-bold tabular-nums">
                {overview ? overview[key] : "—"}
              </p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
