import type { AiSalesDecisionEnvelope } from '../../../ai/sales-decisions/contracts/ai-sales-decision.contract';
import type { TakeoverEligibilityV1 } from '../contracts/takeover-eligibility.contract';

export type TakeoverEligibilityInput = {
  readonly decision: AiSalesDecisionEnvelope;
  readonly operatorTakeoverActive: boolean;
};

export function buildTakeoverEligibility(
  input: TakeoverEligibilityInput,
): TakeoverEligibilityV1 {
  if (input.operatorTakeoverActive) {
    return {
      eligibilityVersion: 'takeover_eligibility@v1',
      takeoverAllowed: true,
      suggestedSuspension: 'operator_takeover_active',
      rationale: 'operator_context_active',
    };
  }
  if (input.decision.policyOutcome === 'escalate_human') {
    return {
      eligibilityVersion: 'takeover_eligibility@v1',
      takeoverAllowed: true,
      suggestedSuspension: 'suggested_hold',
      rationale: 'ai_escalation_policy_signal',
    };
  }
  return {
    eligibilityVersion: 'takeover_eligibility@v1',
    takeoverAllowed: false,
    suggestedSuspension: 'none',
    rationale: 'no_escalation_signal',
  };
}
