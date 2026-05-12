import { UnrecoverableError } from 'bullmq';

/**
 * Non-retryable: bad payload, unknown job type, explicit adapter outcome failure.
 * Retryable: transient network/runtime errors (BullMQ will retry until attempts exhausted).
 */
export function isNonRetryableWorkerError(error: unknown): boolean {
  return error instanceof UnrecoverableError;
}

export function asWorkerThrowable(error: unknown): Error {
  if (error instanceof Error) {
    return error;
  }
  return new Error(String(error));
}
