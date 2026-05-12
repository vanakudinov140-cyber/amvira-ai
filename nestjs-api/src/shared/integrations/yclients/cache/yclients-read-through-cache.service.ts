import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import Redis from 'ioredis';

@Injectable()
export class YclientsReadThroughCacheService {
  private readonly logger = new Logger(YclientsReadThroughCacheService.name);
  private client: Redis | null = null;
  private connectFailed = false;

  constructor(private readonly config: ConfigService) {}

  private getRedis(): Redis | null {
    if (this.connectFailed) {
      return null;
    }
    if (this.client) {
      return this.client;
    }
    try {
      const host = this.config.get<string>('redis.host', 'localhost');
      const port = this.config.get<number>('redis.port', 6379);
      const password = this.config.get<string>('redis.password');
      this.client = new Redis({
        host,
        port,
        password: password || undefined,
        lazyConnect: true,
        maxRetriesPerRequest: 2,
        connectTimeout: 3000,
      });
      return this.client;
    } catch (e) {
      this.connectFailed = true;
      this.logger.warn(
        `yclients_cache_redis_init_failed:${e instanceof Error ? e.message : String(e)}`,
      );
      return null;
    }
  }

  private ttlSeconds(): number {
    return this.config.get<number>('yclients.cacheTtlSeconds') ?? 300;
  }

  async getOrSetJson<T>(
    key: string,
    factory: () => Promise<T>,
  ): Promise<{ readonly value: T; readonly cacheHit: boolean }> {
    const redis = this.getRedis();
    if (!redis) {
      const value = await factory();
      return { value, cacheHit: false };
    }
    try {
      if (redis.status === 'wait') {
        await redis.connect();
      }
      const cached = await redis.get(key);
      if (cached) {
        return { value: JSON.parse(cached) as T, cacheHit: true };
      }
    } catch (e) {
      this.logger.warn(
        `yclients_cache_get_failed:${e instanceof Error ? e.message : String(e)}`,
      );
    }
    const value = await factory();
    try {
      const redis2 = this.getRedis();
      if (redis2) {
        await redis2.set(key, JSON.stringify(value), 'EX', this.ttlSeconds());
      }
    } catch (e) {
      this.logger.warn(
        `yclients_cache_set_failed:${e instanceof Error ? e.message : String(e)}`,
      );
    }
    return { value, cacheHit: false };
  }

  buildKey(parts: readonly string[]): string {
    return ['yclients', 'v1', ...parts].join(':');
  }
}
