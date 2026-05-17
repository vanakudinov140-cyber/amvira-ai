import { Badge } from "@/components/ui/badge";
import { labelStatus } from "@/i18n/ru";
import type { MessageStatus } from "@/types/api";

const statusVariant: Record<
  MessageStatus,
  "secondary" | "default" | "success" | "destructive" | "outline"
> = {
  pending: "outline",
  approved: "default",
  rejected: "destructive",
  sent: "success",
  failed: "destructive",
};

const statusClass: Record<MessageStatus, string> = {
  pending: "border-amber-500/50 bg-amber-500/10 text-amber-200",
  approved: "border-sky-500/50 bg-sky-500/10 text-sky-200",
  rejected: "border-red-500/50 bg-red-500/10 text-red-200",
  sent: "border-emerald-500/50 bg-emerald-500/10 text-emerald-200",
  failed: "border-rose-500/50 bg-rose-500/10 text-rose-200",
};

export function MessageStatusBadge({ status }: { status: MessageStatus }) {
  return (
    <Badge variant={statusVariant[status]} className={statusClass[status]}>
      {labelStatus(status)}
    </Badge>
  );
}
