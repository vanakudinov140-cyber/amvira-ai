import { Global, Module } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AsyncJobsBullModule } from '../../shared/async/bullmq/async-jobs-bull.module';
import { BullMqAsyncJobDispatcher } from '../../shared/async/bullmq/bullmq-async-job.dispatcher';
import { NoopAsyncJobDispatcher } from '../../shared/async/noop-async-job.dispatcher';
import { ASYNC_JOB_DISPATCHER } from '../../shared/async/async-job-dispatcher.contract';
import { INTEGRATION_ADAPTER } from '../../shared/integrations/integration-adapter.contract';
import { NoopIntegrationAdapter } from './noop-integration.adapter';

/**
 * Registers orchestration boundary stubs: async dispatch + integration port.
 * Does not register channel adapter (see {@link ChannelsModule}).
 *
 * {@link ASYNC_JOB_DISPATCHER}: BullMQ when `asyncJobs.useBullmq` is true, else noop (sync ack).
 */
@Global()
@Module({
  imports: [AsyncJobsBullModule],
  providers: [
    NoopAsyncJobDispatcher,
    BullMqAsyncJobDispatcher,
    {
      provide: ASYNC_JOB_DISPATCHER,
      useFactory: (
        config: ConfigService,
        noop: NoopAsyncJobDispatcher,
        bull: BullMqAsyncJobDispatcher,
      ) =>
        config.get<boolean>('asyncJobs.useBullmq') === true ? bull : noop,
      inject: [ConfigService, NoopAsyncJobDispatcher, BullMqAsyncJobDispatcher],
    },
    NoopIntegrationAdapter,
    { provide: INTEGRATION_ADAPTER, useExisting: NoopIntegrationAdapter },
  ],
  exports: [
    ASYNC_JOB_DISPATCHER,
    NoopAsyncJobDispatcher,
    BullMqAsyncJobDispatcher,
    INTEGRATION_ADAPTER,
    NoopIntegrationAdapter,
  ],
})
export class IntegrationsBoundaryModule {}
