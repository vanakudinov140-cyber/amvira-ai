/**
 * Semantic classification of a human intervention — orthogonal to transport command kind.
 */
export const OPERATOR_INTERVENTION_KINDS = [
  'reply',
  'takeover',
  'escalation',
  'stage_transition',
  'suppression_signal',
  'override_ack',
] as const;

export type OperatorInterventionKindV1 =
  (typeof OPERATOR_INTERVENTION_KINDS)[number];
