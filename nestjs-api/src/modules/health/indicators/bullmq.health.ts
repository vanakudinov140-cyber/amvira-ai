import { Injectable, Optional } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { InjectQueue } from '@nestjs/bullmq';
import {
  HealthCheckError,
  HealthIndicator,
  HealthIndicatorResult,
} from '@nestjs/terminus';
import { Queue } from 'bullmq';
import { QueueName } from '../../../common/enums/queue-name.enum';

@Injectable()
export class BullMqHealthIndicator extends HealthIndicator {
  constructor(
    private readonly config: ConfigService,
    @Optional()
    @InjectQueue(QueueName.AsyncJobs)
    private readonly asyncJobsQueue?: Queue,
  ) {
    super();
  }

  async isHealthy(key: string): Promise<HealthIndicatorResult> {
    const useBull = this.config.get<boolean>('asyncJobs.useBullmq') === true;
    if (!useBull) {
      return this.getStatus(key, true, { skipped: true });
    }
    if (!this.asyncJobsQueue) {
      throw new HealthCheckError(
        'BullMQ queue not registered',
        this.getStatus(key, false, { message: 'queue_missing' }),
      );
    }
    try {
      await this.asyncJobsQueue.waitUntilReady();
      return this.getStatus(key, true);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      throw new HealthCheckError(
        'BullMQ check failed',
        this.getStatus(key, false, { message }),
      );
    }
  }
}
