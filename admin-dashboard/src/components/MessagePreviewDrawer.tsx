import { Check, Loader2, Pencil, Sparkles, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { AiReasoningPanel } from "@/components/AiReasoningPanel";
import { MessageStatusBadge } from "@/components/MessageStatusBadge";
import { formatDateTime } from "@/lib/utils";
import { labelAction, labelChannel } from "@/i18n/ru";
import { canModerateStatus } from "@/lib/moderation";
import type { MessageItem } from "@/types/api";

interface MessagePreviewDrawerProps {
  message: MessageItem | null;
  open: boolean;
  busy?: boolean;
  onClose: () => void;
  onEdit: (message: MessageItem) => void;
  onRegenerate?: (id: number) => void;
  onApprove: (id: number) => void;
  onReject: (id: number) => void;
}

export function MessagePreviewDrawer({
  message,
  open,
  busy,
  onClose,
  onEdit,
  onRegenerate,
  onApprove,
  onReject,
}: MessagePreviewDrawerProps) {
  if (!message) return null;

  const moderatable = canModerateStatus(message.status);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={`Сообщение #${message.id}`}
      className="max-w-xl"
    >
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <MessageStatusBadge status={message.status} />
          <Badge variant="outline">{labelAction(message.action)}</Badge>
          <Badge variant="secondary">{labelChannel(message.channel)}</Badge>
        </div>

        <dl className="grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">ID клиента</dt>
            <dd className="font-medium tabular-nums">{message.client_id}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Подготовлено</dt>
            <dd>{formatDateTime(message.prepared_at)}</dd>
          </div>
          {message.sent_at && (
            <div className="sm:col-span-2">
              <dt className="text-muted-foreground">Отправлено</dt>
              <dd>{formatDateTime(message.sent_at)}</dd>
            </div>
          )}
        </dl>

        <AiReasoningPanel message={message} />

        <div className="rounded-lg border border-border bg-muted/20 p-4">
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.text}</p>
        </div>

        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={onClose} disabled={busy}>
            Закрыть
          </Button>
          <Button variant="outline" onClick={() => onEdit(message)} disabled={busy}>
            <Pencil className="h-4 w-4" />
            Редактировать
          </Button>
          {onRegenerate &&
            (message.status === "pending" || message.status === "approved") && (
              <Button
                variant="secondary"
                onClick={() => onRegenerate(message.id)}
                disabled={busy}
              >
                <Sparkles className="h-4 w-4" />
                Перегенерировать
              </Button>
            )}
          {moderatable && (
            <>
              <Button
                variant="destructive"
                onClick={() => onReject(message.id)}
                disabled={busy}
              >
                {busy ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <X className="h-4 w-4" />
                )}
                Отклонить
              </Button>
              <Button
                variant="success"
                onClick={() => onApprove(message.id)}
                disabled={busy}
              >
                {busy ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Check className="h-4 w-4" />
                )}
                Одобрить
              </Button>
            </>
          )}
        </div>
      </div>
    </Dialog>
  );
}
