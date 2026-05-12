/**
 * Structured refusal — no free-text "magic" errors; callers map to HTTP if needed.
 */
export const AI_REFUSAL_REASON = {
  POLICY_DENIED: 'policy.denied',
  CONTENT_FILTER: 'content.filter',
  INSUFFICIENT_CONTEXT: 'insufficient.context',
  PROVIDER_UNAVAILABLE: 'provider.unavailable',
  VALIDATION_FAILED: 'validation.failed',
} as const;

export type AiRefusalReason =
  (typeof AI_REFUSAL_REASON)[keyof typeof AI_REFUSAL_REASON];

export type AiRefusal = {
  readonly reason: AiRefusalReason;
  readonly detail?: string;
};
