import { Injectable } from '@nestjs/common';
import type { ConversationOrchestrationResult } from './conversation-orchestration.result';

const DEFAULT_TTL_MS = 300_000;
const MAX_ENTRIES = 2_000;

type CacheEntry = {
  readonly result: ConversationOrchestrationResult;
  readonly expiresAt: number;
};

/**
 * Process-local duplicate suppression. Not durable across restarts; no Redis/DB.
 * If a second identical key arrives while the first is still executing, both may run
 * (best-effort); cache stores only completed snapshots.
 */
@Injectable()
export class InMemoryConversationIdempotencyGuard {
  private readonly cache = new Map<string, CacheEntry>();

  getCached(turnKey: string): ConversationOrchestrationResult | undefined {
    const entry = this.cache.get(turnKey);
    if (!entry) {
      return undefined;
    }
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(turnKey);
      return undefined;
    }
    return entry.result;
  }

  remember(turnKey: string, result: ConversationOrchestrationResult): void {
    if (this.cache.size >= MAX_ENTRIES) {
      const first = this.cache.keys().next().value;
      if (first !== undefined) {
        this.cache.delete(first);
      }
    }
    this.cache.set(turnKey, {
      result,
      expiresAt: Date.now() + DEFAULT_TTL_MS,
    });
  }

  buildTurnKey(dialogId: string, clientKey: string): string {
    return `${dialogId}:${clientKey}`;
  }
}
