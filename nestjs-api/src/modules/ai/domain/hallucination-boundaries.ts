/**
 * Hallucination boundaries (documentation + stable vocabulary).
 *
 * Policy: model output must not invent facts outside the assembled context snapshot.
 * Only keys present in {@link AiAssembledContext.allowedFactKeys} may ground factual claims.
 */
export const ALLOWED_FACT_SOURCE_KINDS = [
  'dialog.snapshot',
  'client.profile_slice',
  'booking.snapshot',
  'scenario.metadata',
  'retrieval.grounding',
  'yclients.snapshot',
] as const;

export type AllowedFactSourceKind =
  (typeof ALLOWED_FACT_SOURCE_KINDS)[number];
