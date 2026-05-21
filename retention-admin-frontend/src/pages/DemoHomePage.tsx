import { Link, useLocation } from "react-router-dom";
import { Eye, MessageCircle, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const SCENARIOS = [
  "Запись без бронирования",
  "Запись с бронированием",
  "Напоминание за 24 часа",
  "Напоминание за 2 часа",
  "Перенос записи",
  "Отмена записи",
];

export function DemoHomePage() {
  const location = useLocation();
  const notice = (location.state as { notice?: string } | null)?.notice;

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-8">
      {notice ? (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-50">
          {notice}
        </div>
      ) : null}
      <section className="rounded-2xl border border-sky-500/30 bg-sky-500/10 p-6 text-sky-50">
        <div className="flex items-start gap-4">
          <ShieldCheck className="mt-1 h-6 w-6 text-sky-200" />
          <div>
            <h2 className="text-3xl font-semibold tracking-tight">Демонстрация</h2>
            <p className="mt-2 text-sky-100/80">
              Безопасный раздел внутри текущего приложения: только демо-данные, предпросмотр сценариев
              и переход к тестовой отправке в режиме без реальных отправок.
            </p>
          </div>
        </div>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Предпросмотр сценариев</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {SCENARIOS.map((scenario) => (
              <div key={scenario} className="rounded-lg border border-border bg-background p-3 text-sm">
                {scenario}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Перейти в тестовую отправку</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Откройте существующий экран тестовой отправки в demo-режиме: без API, базы данных,
              provider и реальной отправки.
            </p>
            <Link
              to="/demo/test-send"
              className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:opacity-90"
            >
              <MessageCircle className="h-4 w-4" />
              Открыть тестовую отправку
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Посмотреть примеры</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Откройте витрину сообщений, чтобы сравнить сценарии перед запуском.
            </p>
            <Link
              to="/message-preview"
              className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-border bg-muted px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted/80"
            >
              <Eye className="h-4 w-4" />
              Открыть предпросмотр
            </Link>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
