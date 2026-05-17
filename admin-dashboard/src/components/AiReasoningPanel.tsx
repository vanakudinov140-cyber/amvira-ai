import { Brain } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { labelAction, labelSegment, labelTriggerReason } from "@/i18n/ru";
import type { MessageItem, MessageMetadata } from "@/types/api";

interface AiReasoningPanelProps {
  message: MessageItem;
}

export function AiReasoningPanel({ message }: AiReasoningPanelProps) {
  const metadata = message.metadata;
  const explain = message.explain?.length ? message.explain : [];

  return (
    <div className="space-y-3 rounded-lg border border-sky-500/30 bg-sky-500/5 p-4">
      <div className="flex items-center gap-2 text-sm font-medium text-sky-200">
        <Brain className="h-4 w-4" />
        Почему AI выбрал это сообщение
      </div>

      {explain.length > 0 ? (
        <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
          {explain.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">Нет пояснения AI для этого сообщения</p>
      )}

      {metadata && <MetadataGrid metadata={metadata} />}
    </div>
  );
}

function MetadataGrid({ metadata }: { metadata: MessageMetadata }) {
  const items: { label: string; value: string }[] = [
    {
      label: "Дней без визита",
      value: String(metadata.days_since_last_visit ?? "—"),
    },
    {
      label: "Частота визитов",
      value:
        metadata.previous_visit_frequency_days != null
          ? `~${metadata.previous_visit_frequency_days} дн.`
          : "—",
    },
    {
      label: "Сегмент",
      value:
        metadata.client_segment_label ??
        (metadata.client_segment ? labelSegment(metadata.client_segment) : "—"),
    },
    {
      label: "Причина срабатывания",
      value:
        metadata.trigger_reason_label ??
        (metadata.trigger_reason ? labelTriggerReason(metadata.trigger_reason) : "—"),
    },
    {
      label: "Вероятность возврата",
      value:
        metadata.predicted_return_probability != null
          ? `${Math.round(metadata.predicted_return_probability * 100)}%`
          : "—",
    },
    {
      label: "Рекомендуемый сценарий",
      value:
        metadata.recommended_action_label ??
        (metadata.recommended_action ? labelAction(metadata.recommended_action) : "—"),
    },
  ];

  return (
    <div className="grid gap-2 border-t border-border/60 pt-3 sm:grid-cols-2">
      {items.map(({ label, value }) => (
        <div key={label} className="text-xs">
          <span className="text-muted-foreground">{label}: </span>
          <Badge variant="outline" className="ml-1">
            {value}
          </Badge>
        </div>
      ))}
    </div>
  );
}
