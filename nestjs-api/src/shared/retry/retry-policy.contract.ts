/**
 * Retry ownership (architecture):
 * - Transport-level retries (HTTP 5xx, timeouts) belong inside integration/LLM adapters.
 * - Job-level retries (poison messages, business transient) belong to the worker + this policy.
 *
 * This contract is shared; it does not execute retries by itself.
 */
export interface RetryPolicy {
  readonly maxAttempts: number;
  shouldRetry(error: unknown, attempt: number): boolean;
  backoffMs?(attempt: number): number;
}
