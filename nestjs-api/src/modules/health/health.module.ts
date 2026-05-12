import { Module } from '@nestjs/common';
import { TerminusModule } from '@nestjs/terminus';
import { HealthController } from './health.controller';
import { HealthService } from './health.service';
import { BullMqHealthIndicator } from './indicators/bullmq.health';
import { PrismaHealthIndicator } from './indicators/prisma.health';
import { RedisHealthIndicator } from './indicators/redis.health';

@Module({
  imports: [TerminusModule],
  controllers: [HealthController],
  providers: [
    HealthService,
    PrismaHealthIndicator,
    RedisHealthIndicator,
    BullMqHealthIndicator,
  ],
})
export class HealthModule {}
