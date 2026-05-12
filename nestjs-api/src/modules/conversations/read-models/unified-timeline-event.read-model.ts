import type { TimelineActorKind } from './timeline-event-taxonomy';

type TimelineEventBase = {
  readonly timelineEventVersion: 'unified_timeline@v1';
  readonly eventId: string;
  readonly occurredAt: string;
  readonly dialogId: string;
  readonly summary: string;
};

export type TimelineMessageEventV1 = TimelineEventBase & {
  readonly eventKind:
    | 'message.user'
    | 'message.assistant'
    | 'message.system'
    | 'message.tool';
  readonly actorKind: TimelineActorKind;
  readonly correlation: {
    readonly messageId: string;
    readonly role: string;
  };
};

export type TimelineDialogSnapshotEventV1 = TimelineEventBase & {
  readonly eventKind: 'dialog.state_snapshot';
  readonly actorKind: 'system';
  readonly payload: {
    readonly currentStage: string;
    readonly status: string;
    readonly channel: string;
  };
};

export type UnifiedTimelineEventV1 =
  | TimelineMessageEventV1
  | TimelineDialogSnapshotEventV1;
