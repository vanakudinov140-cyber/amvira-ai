import { NavLink, Outlet, useLocation } from "react-router-dom";
import { ApiStatusBadge } from "@/components/ApiStatusBadge";
import { DEMO_MODE, ENV_LABEL } from "@/constants";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const NAV: { to: string; label: string; testLabel: string; end?: boolean }[] = [
  { to: "/", label: "Главная", testLabel: "Главная", end: true },
  { to: "/candidates", label: "Кандидаты", testLabel: "Кандидаты" },
  { to: "/pending", label: "Сообщения", testLabel: "Сообщения" },
  { to: "/sync", label: "Синхронизация", testLabel: "Синхронизация" },
  { to: "/operations", label: "Операции", testLabel: "Операции" },
  { to: "/test-send", label: "Тестовая отправка", testLabel: "Тестовая отправка" },
  { to: "/message-preview", label: "Предпросмотр", testLabel: "Предпросмотр" },
  { to: "/demo", label: "Демонстрация", testLabel: "Демонстрация" },
];

export function AppLayout() {
  const location = useLocation();
  const testSendPage = location.pathname === "/test-send";
  const visibleNav = DEMO_MODE
    ? NAV.filter(({ to }) => ["/demo", "/test-send", "/message-preview"].includes(to))
    : NAV;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/60 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-semibold tracking-tight">
              {DEMO_MODE || testSendPage ? "Панель удержания клиентов" : "AI Retention Admin"}
            </h1>
            <Badge variant="outline" className="border-amber-500/50 text-amber-200">
              {DEMO_MODE ? "Демонстрационная версия" : ENV_LABEL}
            </Badge>
            {DEMO_MODE || testSendPage ? null : <ApiStatusBadge />}
          </div>
          <nav className="flex flex-wrap gap-1">
            {visibleNav.map(({ to, label, testLabel, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn(
                    "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  )
                }
              >
                {DEMO_MODE || testSendPage ? testLabel : label}
              </NavLink>
            ))}
          </nav>
        </div>
        {DEMO_MODE ? (
          <div className="border-t border-sky-500/20 bg-sky-500/10 px-4 py-2 text-center text-sm text-sky-100">
            Демонстрационная версия
          </div>
        ) : null}
      </header>
      <Outlet />
    </div>
  );
}
