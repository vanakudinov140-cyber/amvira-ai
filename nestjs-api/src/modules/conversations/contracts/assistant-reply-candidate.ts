/**
 * AI suggestion materialised for downstream steps — not authoritative until validated + optionally persisted.
 */
export type AssistantReplyCandidate = {
  readonly replyText: string;
  readonly structured: Readonly<Record<string, unknown>>;
  readonly modelId: string;
  readonly schemaId: string;
  readonly schemaVersion: string;
};
