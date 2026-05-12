import type { CorrelationContext } from '../correlation/correlation-context.contract';

export type AsyncJobId = string;

/**
 * Unit of deferred work. Not an application event: describes *what to run later*,
 * not *what already happened* in the domain.
 *
 * Idempotency: producer SHOULD set {@link idempotencyKey}; processor owns dedup semantics.
 */
export type AsyncJob<TPayload extends Record<string, unknown> = Record<string, unknown>> = {
  readonly id: AsyncJobId;
  /** Stable job name for workers (e.g. "ai.generate_reply"). */
  readonly type: string;
  readonly payload: Readonly<TPayload>;
  readonly correlation?: CorrelationContext;
  /** Business-level dedup key for enqueue/outbox processors. */
  readonly idempotencyKey?: string;
};
