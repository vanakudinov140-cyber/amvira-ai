import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import {
  HealthCheckError,
  HealthIndicator,
  HealthIndicatorResult,
} from '@nestjs/terminus';
import Redis from 'ioredis';

@Injectable()
export class RedisHealthIndicator extends HealthIndicator {
  constructor(private readonly config: ConfigService) {
    super();
  }

  async isHealthy(key: string): Promise<HealthIndicatorResult> {
    const host = this.config.get<string>('redis.host', 'localhost');
    const port = this.config.get<number>('redis.port', 6379);
    const password = this.config.get<string>('redis.password');

    const client = new Redis({
      host,
      port,
      password: password || undefined,
      maxRetriesPerRequest: 1,
      connectTimeout: 3000,
      lazyConnect: true,
    });

    try {
      await client.connect();
      const pong = await client.ping();
      if (pong !== 'PONG') {
        throw new Error('Unexpected PING response');
      }
      return this.getStatus(key, true);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      throw new HealthCheckError(
        'Redis check failed',
        this.getStatus(key, false, { message }),
      );
    } finally {
      client.disconnect();
    }
  }
}
