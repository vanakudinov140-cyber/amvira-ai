import type { ConversationTimelineSnapshotV1 } from '../read-models/conversation-timeline-snapshot.read-model';
import type { OperatorApiEnvelopeV1 } from '../operator-http/operator-api-envelope.types';

export type OperatorTimelineHttpDataV1 = {
  readonly timeline: ConversationTimelineSnapshotV1;
  readonly eventCount: number;
  readonly truncated: boolean;
};

export function presentConversationTimeline(
  snapshot: ConversationTimelineSnapshotV1,
  eventLimit: number,
): OperatorApiEnvelopeV1<OperatorTimelineHttpDataV1> {
  const cap = Math.min(Math.max(eventLimit, 10), 2000);
  const truncated = snapshot.events.length > cap;
  const events = truncated
    ? snapshot.events.slice(snapshot.events.length - cap)
    : snapshot.events;
  return {
    apiVersion: 'operator.http@v1',
    data: {
      timeline: {
        ...snapshot,
        events,
      },
      eventCount: events.length,
      truncated,
    },
  };
}
