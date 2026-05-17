import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { updateMessageText } from "@/api/retention";
import { getErrorMessage } from "@/api/client";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import type { MessageItem } from "@/types/api";

interface MessageEditorProps {
  message: MessageItem | null;
  open: boolean;
  onClose: () => void;
  onSaved: (message: MessageItem) => void;
}

export function MessageEditor({
  message,
  open,
  onClose,
  onSaved,
}: MessageEditorProps) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (message) {
      setText(message.text);
      setError(null);
    }
  }, [message]);

  const handleSave = async () => {
    if (!message) return;
    setLoading(true);
    setError(null);
    try {
      const updated = await updateMessageText(message.id, text);
      onSaved(updated);
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={`Редактирование #${message?.id ?? ""}`}
    >
      <div className="space-y-4">
        {error && <Alert variant="destructive">{error}</Alert>}
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={10}
          disabled={loading}
        />
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            Отмена
          </Button>
          <Button onClick={handleSave} disabled={loading || !text.trim()}>
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            Сохранить
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
