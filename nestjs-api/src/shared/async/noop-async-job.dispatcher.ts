import { Injectable } from '@nestjs/common';
import type { AsyncJob } from './async-job.contract';
import type { AsyncJobDispatcher } from './async-job-dispatcher.contract';
import type { AsyncJobDispatchResult } from './async-job-result.contract';

/**
 * No queue, no Redis — immediate ack for wiring tests and local dev.
 */
@Injectable()
export class NoopAsyncJobDispatcher implements AsyncJobDispatcher {
  async dispatch<TPayload extends Record<string, unknown>>(
    job: AsyncJob<TPayload>,
  ): Promise<AsyncJobDispatchResult> {
    return {
      accepted: true,
      jobId: job.id,
      detail: 'noop_dispatcher',
    };
  }
}
