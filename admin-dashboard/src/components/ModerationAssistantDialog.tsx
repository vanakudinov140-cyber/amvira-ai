import { useCallback, useEffect, useState } from "react";
import { Check, Loader2, Sparkles, X } from "lucide-react";
import {
  approveMessage,
  fetchMessageVersions,
  regenerateMessage,
  rejectMessage,
  updateMessageText,
} from "@/api/retention";
import { getErrorMessage } from "@/api/client";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { AiReasoningPanel } from "@/components/AiReasoningPanel";
import { MessageStatusBadge } from "@/components/MessageStatusBadge";
import { Textarea } from "@/components/ui/textarea";
import { labelAction, labelVersionSource } from "@/i18n/ru";
import { canModerateStatus } from "@/lib/moderation";
import { formatDateTime } from "@/lib/utils";
import type { MessageItem, MessageVersionItem } from "@/types/api";

interface ModerationAssistantDialogProps {
  message: MessageItem | null;
  open: boolean;
  onClose: () => void;
  onUpdated: (message: MessageItem) => void;
  onApproved?: (message: MessageItem) => void;
  onRejected?: (message: MessageItem) => void;
}

export function ModerationAssistantDialog({
  message,
  open,
  onClose,
  onUpdated,
  onApproved,
  onRejected,
}: ModerationAssistantDialogProps) {
  const [text, setText] = useState("");
  const [versions, setVersions] = useState<MessageVersionItem[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [moderating, setModerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [current, setCurrent] = useState<MessageItem | null>(message);

  const loadVersions = useCallback(async (messageId: number) => {
    setLoadingVersions(true);
    try {
      const data = await fetchMessageVersions(messageId);
      setVersions(data.items);
    } catch {
      setVersions([]);
    } finally {
      setLoadingVersions(false);
    }
  }, []);

  useEffect(() => {
    if (message && open) {
      setCurrent(message);
      setText(message.text);
      setError(null);
      void loadVersions(message.id);
    }
  }, [message, open, loadVersions]);

  if (!message || !current) return null;

  const moderatable = canModerateStatus(current.status);
  const busy = saving || regenerating || moderating;

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateMessageText(current.id, text);
      setCurrent(updated);
      onUpdated(updated);
      await loadVersions(updated.id);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleRegenerate = async () => {
    setRegenerating(true);
    setError(null);
    try {
      const updated = await regenerateMessage(current.id);
      setText(updated.text);
      setCurrent(updated);
      onUpdated(updated);
      await loadVersions(updated.id);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setRegenerating(false);
    }
  };

  const handleApprove = async () => {
    setModerating(true);
    setError(null);
    try {
      const updated = await approveMessage(current.id);
      onApproved?.(updated);
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setModerating(false);
    }
  };

  const handleReject = async () => {
    setModerating(true);
    setError(null);
    try {
      const updated = await rejectMessage(current.id);
      onRejected?.(updated);
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setModerating(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={`Модерация AI · сообщение #${current.id}`}
      className="max-w-2xl"
    >
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <MessageStatusBadge status={current.status} />
          <Badge variant="outline">{labelAction(current.action)}</Badge>
          <Badge variant="secondary">Клиент #{current.client_id}</Badge>
        </div>

        <AiReasoningPanel message={current} />

        {error && <Alert variant="destructive">{error}</Alert>}

        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={12}
          disabled={busy}
          className="font-mono text-sm"
        />

        <div className="flex flex-wrap gap-2">
          <Button onClick={() => void handleSave()} disabled={busy || !text.trim()}>
            {saving && <Loader2 className="h-4 w-4 animate-spin" />}
            Сохранить
          </Button>
          <Button
            variant="secondary"
            onClick={() => void handleRegenerate()}
            disabled={busy}
          >
            {regenerating ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            Перегенерировать AI
          </Button>
          {moderatable && (
            <>
              <Button
                variant="success"
                onClick={() => void handleApprove()}
                disabled={busy}
              >
                <Check className="h-4 w-4" />
                Одобрить
              </Button>
              <Button
                variant="destructive"
                onClick={() => void handleReject()}
                disabled={busy}
              >
                <X className="h-4 w-4" />
                Отклонить
              </Button>
            </>
          )}
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Закрыть
          </Button>
        </div>

        <div className="space-y-2 border-t border-border pt-4">
          <h3 className="text-sm font-medium">История изменений</h3>
          {loadingVersions ? (
            <p className="text-sm text-muted-foreground">Загрузка истории…</p>
          ) : versions.length === 0 ? (
            <p className="text-sm text-muted-foreground">Пока нет сохранённых версий</p>
          ) : (
            <ul className="max-h-48 space-y-2 overflow-y-auto text-xs">
              {versions.map((v) => (
                <li
                  key={v.id}
                  className="rounded-md border border-border bg-muted/20 p-2"
                >
                  <div className="mb-1 flex flex-wrap gap-2 text-muted-foreground">
                    <Badge variant="outline">{labelVersionSource(v.source)}</Badge>
                    <span>{formatDateTime(v.created_at)}</span>
                  </div>
                  <p className="line-clamp-2 text-muted-foreground">
                    {v.old_content.slice(0, 120)}
                    {v.old_content.length > 120 ? "…" : ""}
                  </p>
                  <p className="mt-1 line-clamp-2">
                    {v.new_content.slice(0, 120)}
                    {v.new_content.length > 120 ? "…" : ""}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Dialog>
  );
}
