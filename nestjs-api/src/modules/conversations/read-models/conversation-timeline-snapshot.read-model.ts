import type { UnifiedTimelineEventV1 } from './unified-timeline-event.read-model';

/**
 * Immutable, composed view for operator workspace — not a live subscription stream.
 */
export type ConversationTimelineSnapshotV1 = {
  readonly snapshotVersion: 'conversation_timeline@v1';
  readonly dialogId: string;
  readonly composedAt: string;
  readonly events: readonly UnifiedTimelineEventV1[];
};
