import { Injectable, Logger } from '@nestjs/common';
import type { Job } from 'bullmq';
import type { AsyncJobBullEnvelope } from '../bullmq/async-job-bull.payload';
import { ASYNC_JOB_MAX_ATTEMPTS } from '../retry/async-job-retry.settings';

/**
 * Final failure hook after BullMQ exhausts attempts. Jobs remain in Redis (removeOnFail cap)
 * for inspection; this is observability only — not a second queue (no Kafka / saga).
 */
@Injectable()
export class AsyncJobDeadLetterLogger {
  private readonly logger = new Logger(AsyncJobDeadLetterLogger.name);

  logFinalFailure(
    job: Job<AsyncJobBullEnvelope, unknown, string> | undefined,
    error: Error,
    _prev: string,
  ): void {
    const data = job?.data;
    this.logger.warn(
      JSON.stringify({
        msg: 'async_job_dead_letter',
        bullJobId: job?.id != null ? String(job.id) : null,
        jobName: job?.name ?? null,
        asyncJobId: data?.asyncJobId ?? null,
        correlationId: data?.correlation?.correlationId ?? null,
        idempotencyKey: data?.idempotencyKey ?? null,
        attemptsMade: job?.attemptsMade ?? null,
        attemptsConfigured: job?.opts?.attempts ?? ASYNC_JOB_MAX_ATTEMPTS,
        error: error.message,
      }),
    );
  }
}
