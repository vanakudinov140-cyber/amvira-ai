import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Lightbulb, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { labelAction, labelSegment } from "@/i18n/ru";
import type { AiPerformance } from "@/types/api";

interface AiPerformanceSectionProps {
  performance: AiPerformance | null;
  loading?: boolean;
}

export function AiPerformanceSection({ performance, loading }: AiPerformanceSectionProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Эффективность AI</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-48 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!performance) {
    return (
      <Card>
        <CardContent className="py-6 text-center text-sm text-muted-foreground">
          Эффективность AI недоступна
        </CardContent>
      </Card>
    );
  }

  const actionChart = performance.top_performing_actions.map((a) => ({
    name: labelAction(a.action),
    returnRate: Math.round(a.return_rate * 100),
    revenue: a.revenue,
  }));

  const segmentChart = Object.entries(performance.return_rate_by_segment).map(
    ([segment, rate]) => ({
      segment: labelSegment(segment),
      returnRate: Math.round(rate * 100),
    }),
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-emerald-400" />
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Эффективность AI и обучение
        </h2>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Доля одобрений AI"
          value={`${Math.round(performance.approval_rate * 100)}%`}
        />
        <MetricCard
          label="Средняя доля правок"
          value={`${performance.average_edit_ratio.toFixed(1)}%`}
        />
        <MetricCard
          label="Возврат клиентов"
          value={`${Math.round(performance.overall_return_rate * 100)}%`}
        />
        <MetricCard
          label="Выручка от AI-сообщений"
          value={`${Math.round(performance.retention_revenue).toLocaleString("ru-RU")} ₽`}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Возврат по сценариям</CardTitle>
          </CardHeader>
          <CardContent className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={actionChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="returnRate" fill="#34d399" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Возврат по сегментам</CardTitle>
          </CardHeader>
          <CardContent className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={segmentChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="segment" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="returnRate" fill="#a78bfa" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ComparisonCard
          title="Правки vs оригинал AI"
          leftLabel="После правки"
          leftRate={performance.edited_vs_original.edited_return_rate}
          leftSent={performance.edited_vs_original.edited_sent}
          rightLabel="Без правок"
          rightRate={performance.edited_vs_original.non_edited_return_rate}
          rightSent={performance.edited_vs_original.non_edited_sent}
        />
        <ComparisonCard
          title="Перегенерация vs первый вариант"
          leftLabel="Перегенерировано"
          leftRate={performance.regenerated_vs_original.regenerated_return_rate}
          leftSent={performance.regenerated_vs_original.regenerated_sent}
          rightLabel="Первый черновик AI"
          rightRate={performance.regenerated_vs_original.original_return_rate}
          rightSent={performance.regenerated_vs_original.original_sent}
        />
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center gap-2">
          <Lightbulb className="h-4 w-4 text-amber-300" />
          <CardTitle className="text-sm">Рекомендации по улучшению</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-inside list-disc space-y-2 text-sm text-muted-foreground">
            {performance.learning_recommendations.map((tip) => (
              <li key={tip}>{tip}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="pt-4">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-xl font-semibold tabular-nums">{value}</p>
      </CardContent>
    </Card>
  );
}

function ComparisonCard({
  title,
  leftLabel,
  leftRate,
  leftSent,
  rightLabel,
  rightRate,
  rightSent,
}: {
  title: string;
  leftLabel: string;
  leftRate: number;
  leftSent: number;
  rightLabel: string;
  rightRate: number;
  rightSent: number;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <p className="text-muted-foreground">{leftLabel}</p>
          <p className="font-medium">
            {Math.round(leftRate * 100)}% возврат · {leftSent} отправлено
          </p>
        </div>
        <div>
          <p className="text-muted-foreground">{rightLabel}</p>
          <p className="font-medium">
            {Math.round(rightRate * 100)}% возврат · {rightSent} отправлено
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

