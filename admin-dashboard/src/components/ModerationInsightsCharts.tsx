import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { labelAction, labelSegment } from "@/i18n/ru";
import type { ModerationInsights } from "@/types/api";

interface ModerationInsightsChartsProps {
  insights: ModerationInsights | null;
  loading?: boolean;
}

export function ModerationInsightsCharts({
  insights,
  loading,
}: ModerationInsightsChartsProps) {
  if (loading) {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardContent className="pt-6">
            <Skeleton className="h-[220px] w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <Skeleton className="h-[220px] w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!insights) {
    return (
      <Card>
        <CardContent className="py-6 text-center text-sm text-muted-foreground">
          Аналитика модерации недоступна
        </CardContent>
      </Card>
    );
  }

  const bySegment = Object.entries(insights.messages_by_segment).map(([segment, count]) => ({
    segment: labelSegment(segment),
    count,
    returnRate: Math.round((insights.return_rate_by_segment[segment] ?? 0) * 100),
  }));

  const topActions = insights.top_performing_actions.map((item) => ({
    action: labelAction(item.action),
    sent: item.sent,
    total: item.total,
  }));

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Сообщения по сегментам</CardTitle>
        </CardHeader>
        <CardContent className="h-[240px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bySegment}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="segment" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#38bdf8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Возврат по сегментам (%)</CardTitle>
        </CardHeader>
        <CardContent className="h-[240px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bySegment}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="segment" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="returnRate" fill="#a78bfa" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="text-sm">Лучшие сценарии</CardTitle>
        </CardHeader>
        <CardContent className="h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topActions}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="action" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="sent" fill="#34d399" name="Отправлено" radius={[4, 4, 0, 0]} />
              <Bar dataKey="total" fill="#64748b" name="Всего" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="text-sm">Модерация AI (одобрено / отклонено)</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-6 text-sm">
          <p>
            Одобрено: <strong className="text-sky-300">{insights.ai_moderation.approved}</strong>
          </p>
          <p>
            Отклонено: <strong className="text-red-300">{insights.ai_moderation.rejected}</strong>
          </p>
          <p>
            На модерации: <strong>{insights.ai_moderation.pending}</strong>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

