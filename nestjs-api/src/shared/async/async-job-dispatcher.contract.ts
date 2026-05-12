import type { AsyncJob } from './async-job.contract';
import type { AsyncJobDispatchResult } from './async-job-result.contract';

export const ASYNC_JOB_DISPATCHER = Symbol('ASYNC_JOB_DISPATCHER');

/**
 * Outbound port for async orchestration. Implementations may be BullMQ later.
 * Application event handlers must not depend on this type — enqueue from services/use-cases only.
 */
export interface AsyncJobDispatcher {
  dispatch<TPayload extends Record<string, unknown>>(
    job: AsyncJob<TPayload>,
  ): Promise<AsyncJobDispatchResult>;
}
