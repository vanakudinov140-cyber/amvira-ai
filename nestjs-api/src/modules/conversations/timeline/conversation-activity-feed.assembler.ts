import type { Dialog, Message } from '@prisma/client';
import type { TimelineActorKind } from '../read-models/timeline-event-taxonomy';
import type {
  TimelineDialogSnapshotEventV1,
  TimelineMessageEventV1,
} from '../read-models/unified-timeline-event.read-model';

const SUMMARY_MAX = 280;

function truncate(text: string): string {
  const t = text.trim();
  if (t.length <= SUMMARY_MAX) {
    return t;
  }
  return `${t.slice(0, SUMMARY_MAX)}…`;
}

function actorForRole(role: Message['role']): TimelineActorKind {
  switch (role) {
    case 'USER':
      return 'human';
    case 'ASSISTANT':
      return 'ai';
    case 'SYSTEM':
      return 'system';
    case 'TOOL':
      return 'tool';
    default:
      return 'unknown';
  }
}

function kindForRole(
  role: Message['role'],
): TimelineMessageEventV1['eventKind'] {
  switch (role) {
    case 'USER':
      return 'message.user';
    case 'ASSISTANT':
      return 'message.assistant';
    case 'SYSTEM':
      return 'message.system';
    case 'TOOL':
      return 'message.tool';
    default:
      return 'message.system';
  }
}

export function assembleMessageTimelineEvent(
  message: Message,
): TimelineMessageEventV1 {
  return {
    timelineEventVersion: 'unified_timeline@v1',
    eventId: `msg:${message.id}`,
    occurredAt: message.createdAt.toISOString(),
    dialogId: message.dialogId,
    summary: truncate(message.content),
    eventKind: kindForRole(message.role),
    actorKind: actorForRole(message.role),
    correlation: {
      messageId: message.id,
      role: message.role,
    },
  };
}

export function assembleDialogSnapshotTimelineEvent(
  dialog: Dialog,
  composedAtIso: string,
): TimelineDialogSnapshotEventV1 {
  return {
    timelineEventVersion: 'unified_timeline@v1',
    eventId: `dialog:${dialog.id}:snapshot`,
    occurredAt: composedAtIso,
    dialogId: dialog.id,
    summary: `Dialog ${dialog.status} · stage ${String(dialog.currentStage)}`,
    eventKind: 'dialog.state_snapshot',
    actorKind: 'system',
    payload: {
      currentStage: String(dialog.currentStage),
      status: String(dialog.status),
      channel: String(dialog.channel),
    },
  };
}
