export type AiHealthSummaryReadModelV1 = {
  readonly version: 'ai_health_summary@v1';
  readonly source: 'message_corpus';
  readonly hasAssistantTurn: boolean;
  readonly lastAssistantExcerpt?: string;
  readonly lastAssistantAtIso?: string;
  /** Heuristic: last row is USER after at least one assistant turn → likely pending generation/review. */
  readonly stalledHint: boolean;
};

export type AiVisibilitySnapshotV1 = AiHealthSummaryReadModelV1;
