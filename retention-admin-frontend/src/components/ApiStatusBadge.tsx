import { useCallback, useEffect, useState } from "react";
import { apiClient } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type Status = "checking" | "online" | "offline";

export function ApiStatusBadge() {
  const [status, setStatus] = useState<Status>("checking");

  const check = useCallback(async () => {
    setStatus("checking");
    try {
      const { data } = await apiClient.get<{ status?: string }>("/health", {
        timeout: 15_000,
      });
      setStatus(data?.status === "ok" ? "online" : "offline");
    } catch {
      setStatus("offline");
    }
  }, []);

  useEffect(() => {
    void check();
    const id = window.setInterval(() => void check(), 60_000);
    return () => window.clearInterval(id);
  }, [check]);

  const label =
    status === "checking"
      ? "API…"
      : status === "online"
        ? "API online"
        : "API offline";

  return (
    <Badge
      variant="outline"
      className={cn(
        "cursor-default text-xs font-normal",
        status === "online" && "border-emerald-500/40 text-emerald-300",
        status === "offline" && "border-red-500/40 text-red-300",
        status === "checking" && "border-muted-foreground/30 text-muted-foreground",
      )}
      title={apiClient.defaults.baseURL}
    >
      {label}
    </Badge>
  );
}
