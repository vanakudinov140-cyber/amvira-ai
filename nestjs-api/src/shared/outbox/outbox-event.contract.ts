import type { CorrelationContext } from '../correlation/correlation-context.contract';

/**
 * Outbox-ready envelope — persistence and relay are future concerns.
 * Differs from application events: explicit aggregate routing for reliable publish.
 */
export type OutboxEvent<TPayload extends Record<string, unknown> = Record<string, unknown>> = {
  readonly eventId: string;
  readonly aggregateType: string;
  readonly aggregateId: string;
  readonly type: string;
  readonly payload: Readonly<TPayload>;
  readonly occurredAt: Date;
  readonly correlation?: CorrelationContext;
};
