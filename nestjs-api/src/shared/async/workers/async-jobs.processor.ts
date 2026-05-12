import { Inject, Injectable, Logger } from '@nestjs/common';
import { OnWorkerEvent, Processor, WorkerHost } from '@nestjs/bullmq';
import type { Job } from 'bullmq';
import { UnrecoverableError } from 'bullmq';
import { QueueName } from '../../../common/enums/queue-name.enum';
import type { ChannelAdapter } from '../../../modules/channels/channel-adapter.contract';
import { CHANNEL_ADAPTER } from '../../../modules/channels/channel-adapter.contract';
import type { AsyncJobBullEnvelope } from '../bullmq/async-job-bull.payload';
import { AsyncJobDeadLetterLogger } from '../dead-letter/async-job-dead-letter.logger';
import { asWorkerThrowable } from '../retry/async-job-failure.classifier';
import { DefaultAsyncJobRetryPolicy } from '../retry/default-async-job.retry-policy';

const CHANNEL_DELIVER = 'channel.deliver' as const;

@Processor(QueueName.AsyncJobs)
@Injectable()
export class AsyncJobsProcessor extends WorkerHost {
  private readonly logger = new Logger(AsyncJobsProcessor.name);

  constructor(
    @Inject(CHANNEL_ADAPTER) private readonly channel: ChannelAdapter,
    private readonly deadLetter: AsyncJobDeadLetterLogger,
    private readonly retryPolicy: DefaultAsyncJobRetryPolicy,
  ) {
    super();
  }

  async process(
    job: Job<AsyncJobBullEnvelope, void, string>,
  ): Promise<void> {
    const base = {
      msg: 'async_job_start',
      bullJobId: String(job.id),
      jobName: job.name,
      asyncJobId: job.data.asyncJobId,
      correlationId: job.data.correlation?.correlationId ?? null,
      idempotencyKey: job.data.idempotencyKey ?? null,
      maxAttempts: this.retryPolicy.maxAttempts,
    };
    this.logger.log(JSON.stringify(base));

    try {
      switch (job.name) {
        case CHANNEL_DELIVER:
          await this.runChannelDeliver(job);
          break;
        default:
          throw new UnrecoverableError(`unknown_async_job_type:${job.name}`);
      }
      this.logger.log(
        JSON.stringify({
          ...base,
          msg: 'async_job_complete',
        }),
      );
    } catch (e) {
      const err = asWorkerThrowable(e);
      this.logger.warn(
        JSON.stringify({
          ...base,
          msg: 'async_job_attempt_failed',
          error: err.message,
          unrecoverable: e instanceof UnrecoverableError,
        }),
      );
      throw err;
    }
  }

  @OnWorkerEvent('failed')
  onFailed(
    job: Job<AsyncJobBullEnvelope, unknown, string> | undefined,
    error: Error,
    prev: string,
  ): void {
    this.deadLetter.logFinalFailure(job, error, prev);
  }

  private async runChannelDeliver(
    job: Job<AsyncJobBullEnvelope, void, string>,
  ): Promise<void> {
    const p = job.data.payload;
    const body = p.body;
    const idempotencyKey = p.idempotencyKey;
    if (typeof body !== 'string' || typeof idempotencyKey !== 'string') {
      throw new UnrecoverableError('channel_deliver_invalid_payload');
    }
    const metadata =
      p.channelMetadata !== undefined &&
      p.channelMetadata !== null &&
      typeof p.channelMetadata === 'object' &&
      !Array.isArray(p.channelMetadata)
        ? (p.channelMetadata as Readonly<Record<string, unknown>>)
        : undefined;

    const receipt = await this.channel.deliver({
      body,
      idempotencyKey,
      correlation: job.data.correlation,
      metadata,
    });

    if (receipt.status === 'failed') {
      throw new UnrecoverableError(
        receipt.detail ?? 'channel_deliver_receipt_failed',
      );
    }
  }
}
