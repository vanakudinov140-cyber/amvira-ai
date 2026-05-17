import { X } from "lucide-react";
import { useToast, type ToastVariant } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

const variantStyles: Record<ToastVariant, string> = {
  default: "border-border bg-card",
  success: "border-success/40 bg-success/10",
  destructive: "border-destructive/40 bg-destructive/10",
};

export function Toaster() {
  const { toasts, dismiss } = useToast();

  return (
    <div className="pointer-events-none fixed bottom-0 right-0 z-[100] flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:max-w-[420px]">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "pointer-events-auto rounded-lg border p-4 shadow-lg backdrop-blur",
            variantStyles[t.variant ?? "default"],
          )}
        >
          <div className="flex items-start gap-3">
            <div className="flex-1 space-y-1">
              <p className="text-sm font-semibold">{t.title}</p>
              {t.description && (
                <p className="text-sm text-muted-foreground">{t.description}</p>
              )}
            </div>
            <button
              type="button"
              onClick={() => dismiss(t.id)}
              className="rounded-md p-1 text-muted-foreground hover:bg-muted"
              aria-label="Закрыть"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
