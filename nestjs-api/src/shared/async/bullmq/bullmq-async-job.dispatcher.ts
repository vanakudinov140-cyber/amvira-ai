import { Injectable, Logger } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bullmq';
import type { JobsOptions } from 'bullmq';
import type { Queue } from 'bullmq';
import { QueueName } from '../../../common/enums/queue-name.enum';
import type { AsyncJob } from '../async-job.contract';
import type { AsyncJobDispatcher } from '../async-job-dispatcher.contract';
import type { AsyncJobDispatchResult } from '../async-job-result.contract';
import type { AsyncJobBullEnvelope } from './async-job-bull.payload';

@Injectable()
export class BullMqAsyncJobDispatcher implements AsyncJobDispatcher {
  private readonly logger = new Logger(BullMqAsyncJobDispatcher.name);

  constructor(
    @InjectQueue(QueueName.AsyncJobs)
    private readonly queue: Queue,
  ) {}

  async dispatch<TPayload extends Record<string, unknown>>(
    job: AsyncJob<TPayload>,
  ): Promise<AsyncJobDispatchResult> {
    const envelope: AsyncJobBullEnvelope = {
      asyncJobId: job.id,
      payload: job.payload,
      correlation: job.correlation,
      idempotencyKey: job.idempotencyKey,
    };

    const opts: JobsOptions = {
      jobId: job.idempotencyKey ?? job.id,
    };

    try {
      const bullJob = await this.queue.add(job.type, envelope, opts);
      const bullId = bullJob.id != null ? String(bullJob.id) : job.id;
      this.logger.log(
        JSON.stringify({
          msg: 'async_job_enqueued',
          asyncJobId: job.id,
          bullJobId: bullId,
          jobType: job.type,
          correlationId: job.correlation?.correlationId ?? null,
          idempotencyKey: job.idempotencyKey ?? null,
        }),
      );
      return {
        accepted: true,
        jobId: bullId,
        detail: 'bullmq_enqueued',
      };
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      this.logger.warn(
        JSON.stringify({
          msg: 'async_job_enqueue_failed',
          asyncJobId: job.id,
          jobType: job.type,
          correlationId: job.correlation?.correlationId ?? null,
          error: message,
        }),
      );
      return {
        accepted: false,
        jobId: job.id,
        detail: `enqueue_error:${message}`,
      };
    }
  }
}
