import { ShieldAlert } from "lucide-react";
import type { AutomationSettings } from "@/types/api";

interface TestModeBannerProps {
  automation: AutomationSettings | null;
}

export function TestModeBanner({ automation }: TestModeBannerProps) {
  if (!automation?.test_mode) return null;

  return (
    <div className="border-b border-amber-500/40 bg-amber-500/15 px-4 py-3">
      <div className="mx-auto flex max-w-7xl items-start gap-3">
        <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-300" />
        <div className="space-y-1">
          <p className="text-sm font-semibold text-amber-100">
            Включён безопасный тестовый режим
          </p>
          <p className="text-xs text-amber-200/90">
            Массовая рассылка ограничена: send-pending отправляет только на{" "}
            {automation.test_recipients.join(", ") || "TEST_RECIPIENTS"} (макс.{" "}
            {automation.send_pending_limit} за запуск).
          </p>
        </div>
      </div>
    </div>
  );
}
