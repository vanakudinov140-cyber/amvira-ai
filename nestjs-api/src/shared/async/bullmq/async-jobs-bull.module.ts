import { Module } from '@nestjs/common';
import { QueueModule } from '../../../modules/queue/queue.module';
import { BullMqAsyncJobDispatcher } from './bullmq-async-job.dispatcher';
import { AsyncJobDeadLetterLogger } from '../dead-letter/async-job-dead-letter.logger';
import { DefaultAsyncJobRetryPolicy } from '../retry/default-async-job.retry-policy';
import { AsyncJobsProcessor } from '../workers/async-jobs.processor';

/**
 * BullMQ-backed async job transport + worker. Redis connection comes from {@link BullModule.forRootAsync}.
 */
@Module({
  imports: [QueueModule],
  providers: [
    BullMqAsyncJobDispatcher,
    AsyncJobsProcessor,
    AsyncJobDeadLetterLogger,
    DefaultAsyncJobRetryPolicy,
  ],
  exports: [BullMqAsyncJobDispatcher],
})
export class AsyncJobsBullModule {}
