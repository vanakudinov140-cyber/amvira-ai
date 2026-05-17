import { NavLink, Outlet } from "react-router-dom";
import { ENV_LABEL } from "@/constants";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const NAV: { to: string; label: string; end?: boolean }[] = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/candidates", label: "Retention Candidates" },
  { to: "/pending", label: "Pending Messages" },
  { to: "/sync", label: "Sync Controls" },
];

export function AppLayout() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/60 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-semibold tracking-tight">AI Retention Admin</h1>
            <Badge variant="outline" className="border-amber-500/50 text-amber-200">
              {ENV_LABEL}
            </Badge>
          </div>
          <nav className="flex flex-wrap gap-1">
            {NAV.map(({ to, label, end }) => (
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
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
