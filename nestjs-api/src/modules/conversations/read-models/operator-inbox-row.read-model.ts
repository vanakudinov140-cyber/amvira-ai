import type { ConversationTimelineSnapshotV1 } from './conversation-timeline-snapshot.read-model';
import type { OperatorInboxUnreadSignalsV1 } from './operator-inbox-unread-signals.read-model';
import type { AiVisibilitySnapshotV1 } from './visibility/ai-visibility-snapshot.read-model';
import type { DeliveryVisibilitySnapshotV1 } from './visibility/delivery-visibility-snapshot.read-model';
import type { EscalationVisibilityV1 } from './visibility/escalation-visibility.read-model';
import type { HandoffTakeoverVisibilityV1 } from './visibility/handoff-takeover-visibility.read-model';
import type { ToolExecutionVisibilitySnapshotV1 } from './visibility/tool-execution-visibility-snapshot.read-model';

export type OperatorInboxRowV1 = {
  readonly rowVersion: 'operator_inbox_row@v1';
  readonly dialogId: string;
  readonly clientId: string;
  readonly channel: string;
  readonly currentStage: string;
  readonly dialogStatus: string;
  readonly updatedAtIso: string;
  readonly lastMessageAtIso?: string;
  readonly unreadSignals: OperatorInboxUnreadSignalsV1;
  readonly handoffTakeover: HandoffTakeoverVisibilityV1;
  readonly escalation: EscalationVisibilityV1;
  readonly delivery: DeliveryVisibilitySnapshotV1;
  readonly aiVisibility: AiVisibilitySnapshotV1;
  readonly toolExecution: ToolExecutionVisibilitySnapshotV1;
  readonly timeline: ConversationTimelineSnapshotV1;
};
