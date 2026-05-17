import { useCallback, useEffect, useRef, useState } from "react";
import { REFRESH_MS } from "@/constants";

export function useAutoRefresh(onRefresh: () => void | Promise<void>) {
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);
  const onRefreshRef = useRef(onRefresh);
  onRefreshRef.current = onRefresh;

  const refresh = useCallback(async (silent = false) => {
    if (!silent) setRefreshing(true);
    try {
      await onRefreshRef.current();
      setLastRefreshedAt(new Date());
    } finally {
      if (!silent) setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void refresh(false);
    const timer = window.setInterval(() => void refresh(true), REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [refresh]);

  return { refreshing, lastRefreshedAt, refresh };
}
