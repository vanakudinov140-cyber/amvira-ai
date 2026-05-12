import type { AiConfidenceRoutingV1 } from './ai-confidence-routing.contract';
import type { EscalationIntentV1 } from './escalation-intent.contract';
import type { EscalationQueueItemV1 } from './escalation-queue.contract';
import type { HumanHandoffDecisionV1 } from './human-handoff-decision.contract';
import type { InterventionResultV1 } from './intervention-result.contract';
import type { OperatorAssistSignalsV1 } from './operator-assist.contract';
import type { TakeoverEligibilityV1 } from './takeover-eligibility.contract';
import type { TakeoverStateV1 } from './takeover.contract';

export type ManualBookingApprovalState =
  | 'idle'
  | 'pending_operator'
  | 'approved'
  | 'rejected';

export type ManualBookingApprovalFlowV1 = {
  readonly flowVersion: 'manual_booking_approval@v1';
  readonly dialogId: string;
  readonly state: ManualBookingApprovalState;
  readonly reason?: string;
};

export type OperationsEnvelopeV1 = {
  readonly envelopeVersion: 'operations@v1';
  readonly dialogId: string;
  readonly composedAt: string;
  readonly routing: AiConfidenceRoutingV1;
  readonly takeoverEligibility: TakeoverEligibilityV1;
  readonly takeoverState: TakeoverStateV1;
  readonly escalationIntent?: EscalationIntentV1;
  readonly handoffDecision?: HumanHandoffDecisionV1;
  readonly escalationQueueItem?: EscalationQueueItemV1;
  readonly manualBookingApproval?: ManualBookingApprovalFlowV1;
  readonly intervention: InterventionResultV1;
  /** Non-authoritative hints for operators; never auto-executed. */
  readonly operatorAssist?: OperatorAssistSignalsV1;
};
