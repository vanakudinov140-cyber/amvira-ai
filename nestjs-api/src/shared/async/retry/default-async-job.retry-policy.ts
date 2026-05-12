import type { RetryPolicy } from '../../retry/retry-policy.contract';
import {
  ASYNC_JOB_BACKOFF_MS,
  ASYNC_JOB_MAX_ATTEMPTS,
} from './async-job-retry.settings';

/**
 * Mirrors BullMQ defaults on the async-jobs queue. Used for explicit classification
 * in workers (documentation + optional guards); transport still applies attempts/backoff.
 */
export class DefaultAsyncJobRetryPolicy implements RetryPolicy {
  readonly maxAttempts = ASYNC_JOB_MAX_ATTEMPTS;

  shouldRetry(_error: unknown, attempt: number): boolean {
    return attempt < this.maxAttempts;
  }

  backoffMs(attempt: number): number {
    if (attempt < 1) {
      return ASYNC_JOB_BACKOFF_MS;
    }
    return ASYNC_JOB_BACKOFF_MS * 2 ** (attempt - 1);
  }
}
