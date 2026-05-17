import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { labelAction, labelStatus } from "@/i18n/ru";
import type { RetentionOverview } from "@/types/api";

const ACTION_COLORS = ["#38bdf8", "#a78bfa", "#fbbf24", "#34d399"];

interface AnalyticsChartsProps {
  overview: RetentionOverview | null;
  loading?: boolean;
}

export function AnalyticsCharts({ overview, loading }: AnalyticsChartsProps) {
  if (loading) {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <Skeleton className="h-4 w-40" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-[240px] w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-4 w-40" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-[240px] w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!overview) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-muted-foreground">
          Аналитика недоступна — проверьте URL API и CORS
        </CardContent>
      </Card>
    );
  }

  const actionData = [
    { name: labelAction("monthly_care"), value: overview.actions_breakdown.monthly_care },
    { name: labelAction("gentle_return"), value: overview.actions_breakdown.gentle_return },
    {
      name: labelAction("comeback_reminder"),
      value: overview.actions_breakdown.comeback_reminder,
    },
    { name: labelAction("winback"), value: overview.actions_breakdown.winback },
  ];

  const statusData = [
    { name: labelStatus("pending"), value: overview.messages_pending },
    { name: labelStatus("approved"), value: overview.messages_approved },
    { name: labelStatus("sent"), value: overview.messages_sent },
    { name: labelStatus("rejected"), value: overview.messages_rejected },
  ];

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Распределение по сценариям</CardTitle>
        </CardHeader>
        <CardContent className="h-[260px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={actionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: "#0f172a",
                  border: "1px solid #334155",
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {actionData.map((_, i) => (
                  <Cell key={i} fill={ACTION_COLORS[i % ACTION_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Воронка сообщений по статусам</CardTitle>
        </CardHeader>
        <CardContent className="h-[260px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={statusData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={90}
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
              >
                {statusData.map((_, i) => (
                  <Cell key={i} fill={ACTION_COLORS[i % ACTION_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "#0f172a",
                  border: "1px solid #334155",
                  borderRadius: 8,
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
