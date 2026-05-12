/**
 * Stable scope identifiers — used for ordering, tracing, and fact key prefixes.
 */
export const RETRIEVAL_SCOPES = [
  'static.catalog',
  'salon.config',
  'yclients.availability',
  'scenario.metadata',
  'dialog.snapshot',
  'recent.messages',
  'booking.summaries',
] as const;

export type RetrievalScope = (typeof RETRIEVAL_SCOPES)[number];
