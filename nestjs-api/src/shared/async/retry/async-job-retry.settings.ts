/**
 * Single source of truth for async-job queue retries (BullMQ + {@link DefaultAsyncJobRetryPolicy}).
 */
export const ASYNC_JOB_MAX_ATTEMPTS = 5;
export const ASYNC_JOB_BACKOFF_MS = 2000;
export const ASYNC_JOB_BACKOFF_TYPE = 'exponential' as const;
/** Retain failed jobs for operator inspection / future DLQ tooling. */
export const ASYNC_JOB_REMOVE_ON_FAIL_COUNT = 500;
