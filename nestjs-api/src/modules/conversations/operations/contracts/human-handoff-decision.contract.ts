import type { EscalationReasonCode } from './escalation-reasons.taxonomy';

export type HumanHandoffDecisionV1 = {
  readonly decisionVersion: 'human_handoff@v1';
  readonly dialogId: string;
  readonly decidedAt: string;
  /**
   * True only after explicit operator / control-plane confirmation
   * ({@link OperatorOrchestrationContextV1.confirmEscalationToQueue}) — never from AI-only inference.
   */
  readonly routeToOperatorQueue: boolean;
  readonly reasonCode: EscalationReasonCode;
  readonly recoverability: 'recoverable' | 'non_recoverable';
};
