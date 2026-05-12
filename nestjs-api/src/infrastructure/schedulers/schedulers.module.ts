import { Module } from '@nestjs/common';

/**
 * Infrastructure entry for scheduled jobs (e.g. @nestjs/schedule).
 * Register cron providers and queue consumers here or in dedicated worker processes.
 */
@Module({})
export class SchedulersModule {}
