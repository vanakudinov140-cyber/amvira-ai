/**
 * Future: pre/post generation moderation (policies separate from {@link LlmClient}).
 */
export interface AiModerationLayer {
  evaluateDraft(text: string): Promise<{ allowed: boolean; reason?: string }>;
}
