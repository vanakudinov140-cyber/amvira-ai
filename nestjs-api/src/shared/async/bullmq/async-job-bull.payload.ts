import type { CorrelationContext } from '../../correlation/correlation-context.contract';

/**
 * BullMQ-serializable envelope (Redis). Keeps correlation + idempotency for workers/logs.
 */
export type AsyncJobBullEnvelope = {
  readonly asyncJobId: string;
  readonly payload: Readonly<Record<string, unknown>>;
  readonly correlation?: CorrelationContext;
  readonly idempotencyKey?: string;
};
