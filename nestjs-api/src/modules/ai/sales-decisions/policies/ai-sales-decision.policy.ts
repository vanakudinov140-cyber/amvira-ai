import { evaluateStageTransition } from '../../../dialogs/domain/dialog-stage.policy';
import type { DialogStageCode } from '../../../dialogs/domain/dialog-stage.types';
import type { AiSalesTransitionProposal } from '../contracts/ai-sales-decision.contract';
import type {
  AiSalesDecisionPolicyOutcome,
  AiSalesObjectionProfile,
} from '../contracts/ai-sales-decision.contract';

/**
 * Centralized rules: AI never mutates stages; proposals are validated against FSM transition matrix.
 */
export class AiSalesDecisionPolicy {
  proposeTransition(
    from: DialogStageCode,
    to: DialogStageCode,
    rationale: string,
  ): AiSalesTransitionProposal | null {
    if (evaluateStageTransition(from, to) !== null) {
      return null;
    }
    return { fromStage: from, toStage: to, rationale };
  }

  evaluatePolicyOutcome(input: {
    readonly dialogStatus: string;
    readonly objection: AiSalesObjectionProfile;
    readonly overallConfidence: number;
    readonly hasLegalProposal: boolean;
  }): {
    outcome: AiSalesDecisionPolicyOutcome;
    suppressedReason?: string;
    escalation?: { reason: string };
  } {
    if (input.dialogStatus === 'CLOSED') {
      return {
        outcome: 'suppress',
        suppressedReason: 'dialog_closed',
      };
    }
    if (
      input.objection.detected &&
      input.objection.severity === 'high' &&
      input.overallConfidence < 0.35
    ) {
      return {
        outcome: 'escalate_human',
        escalation: { reason: 'high_objection_low_confidence' },
      };
    }
    if (!input.hasLegalProposal && input.overallConfidence < 0.25) {
      return {
        outcome: 'suppress',
        suppressedReason: 'low_signal_strength',
      };
    }
    return { outcome: 'propose' };
  }
}
