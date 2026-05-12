/**
 * Future: retry orchestration around {@link LlmClient.generate} (no queue implied).
 */
export interface AiRetryPolicy {
  readonly maxAttempts: number;
  shouldRetry(error: unknown, attempt: number): boolean;
}
