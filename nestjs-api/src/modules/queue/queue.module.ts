import { BullModule } from '@nestjs/bullmq';
import { Global, Module } from '@nestjs/common';
import { QueueName } from '../../common/enums/queue-name.enum';
import {
  ASYNC_JOB_BACKOFF_MS,
  ASYNC_JOB_BACKOFF_TYPE,
  ASYNC_JOB_MAX_ATTEMPTS,
  ASYNC_JOB_REMOVE_ON_FAIL_COUNT,
} from '../../shared/async/retry/async-job-retry.settings';

@Global()
@Module({
  imports: [
    BullModule.registerQueue({
      name: QueueName.Default,
    }),
    BullModule.registerQueue({
      name: QueueName.AsyncJobs,
      defaultJobOptions: {
        attempts: ASYNC_JOB_MAX_ATTEMPTS,
        backoff: { type: ASYNC_JOB_BACKOFF_TYPE, delay: ASYNC_JOB_BACKOFF_MS },
        removeOnComplete: true,
        removeOnFail: ASYNC_JOB_REMOVE_ON_FAIL_COUNT,
      },
    }),
  ],
  exports: [BullModule],
})
export class QueueModule {}
