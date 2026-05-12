/**
 * Stable taxonomy for escalation / handoff — not LLM-free-form strings in domain code.
 */
export const ESCALATION_REASON_CODES = [
  'high_objection_low_confidence',
  'operator_requested',
  'policy_violation_suspected',
  'booking_manual_review_required',
  'client_distress',
  'technical_failure',
  'unspecified',
] as const;

export type EscalationReasonCode = (typeof ESCALATION_REASON_CODES)[number];
