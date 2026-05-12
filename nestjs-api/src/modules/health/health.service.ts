import { Injectable } from '@nestjs/common';
import { HealthCheckService } from '@nestjs/terminus';
import { BullMqHealthIndicator } from './indicators/bullmq.health';
import { PrismaHealthIndicator } from './indicators/prisma.health';
import { RedisHealthIndicator } from './indicators/redis.health';

@Injectable()
export class HealthService {
  constructor(
    private readonly health: HealthCheckService,
    private readonly prismaHealth: PrismaHealthIndicator,
    private readonly redisHealth: RedisHealthIndicator,
    private readonly bullMqHealth: BullMqHealthIndicator,
  ) {}

  getLivePayload() {
    return {
      status: 'live',
      service: 'nestjs-api',
      timestamp: new Date().toISOString(),
      uptimeSeconds: Math.round(process.uptime()),
    };
  }

  runReadyChecks() {
    return this.health.check([
      () => this.prismaHealth.isHealthy('postgres'),
      () => this.redisHealth.isHealthy('redis'),
      () => this.bullMqHealth.isHealthy('bullmq_async_jobs'),
    ]);
  }

  /** @deprecated Prefer {@link runReadyChecks} via GET /health/ready */
  runHealthChecks() {
    return this.runReadyChecks();
  }
}
