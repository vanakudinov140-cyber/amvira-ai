import { Injectable } from '@nestjs/common';
import {
  HealthCheckError,
  HealthIndicator,
  HealthIndicatorResult,
} from '@nestjs/terminus';
import { PrismaService } from '../../../infrastructure/persistence/prisma.service';

@Injectable()
export class PrismaHealthIndicator extends HealthIndicator {
  constructor(private readonly prisma: PrismaService) {
    super();
  }

  async isHealthy(key: string): Promise<HealthIndicatorResult> {
    try {
      await this.prisma.$queryRaw`SELECT 1`;
      return this.getStatus(key, true, { engine: 'postgres' });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      throw new HealthCheckError(
        'Prisma check failed',
        this.getStatus(key, false, { message }),
      );
    }
  }
}
