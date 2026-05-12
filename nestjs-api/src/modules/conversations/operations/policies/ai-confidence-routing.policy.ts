import type { AiSalesDecisionEnvelope } from '../../../ai/sales-decisions/contracts/ai-sales-decision.contract';
import type { AiConfidenceRoutingV1 } from '../contracts/ai-confidence-routing.contract';

export function buildAiConfidenceRouting(
  decision: AiSalesDecisionEnvelope,
): AiConfidenceRoutingV1 {
  const overall = decision.confidence.overall;
  const escalate = decision.policyOutcome === 'escalate_human';
  const suggestReview = overall < 0.45 || escalate;
  const suggestQueue = escalate || overall < 0.3;
  return {
    routingVersion: 'ai_confidence_routing@v1',
    overallConfidence: overall,
    suggestOperatorReview: suggestReview,
    suggestQueueEscalation: suggestQueue,
    rationale: escalate
      ? 'sales_policy_escalation'
      : suggestReview
        ? 'low_or_moderate_confidence'
        : 'confidence_acceptable',
  };
}
