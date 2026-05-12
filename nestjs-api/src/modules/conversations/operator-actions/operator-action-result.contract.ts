import type { OperatorAssistantSuppressionSignalV1 } from '../operator-contracts/operator-assistant-suppression.contract';
import type { OperatorTakeoverStateV1 } from '../operator-contracts/operator-takeover-state.contract';
import type { OperatorAuditSnapshotV1 } from '../operator-audit/operator-audit-snapshot.contract';

export type OperatorActionOrchestrationResultV1 = {
  readonly resultVersion: 'operator_action_orchestration@v1';
  readonly status: 'completed' | 'rejected' | 'failed';
  readonly rejection?: Readonly<{
    readonly code: string;
    readonly detail?: string;
  }>;
  readonly transientTakeover?: OperatorTakeoverStateV1;
  readonly transientSuppression?: OperatorAssistantSuppressionSignalV1;
  /** Transient hint for gateways to clear operator takeover on next orchestration request. */
  readonly resumeAssistantSuggested?: boolean;
  readonly audit: OperatorAuditSnapshotV1;
};
