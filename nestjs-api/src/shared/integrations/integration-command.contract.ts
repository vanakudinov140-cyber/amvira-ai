import type { CorrelationContext } from '../correlation/correlation-context.contract';

/**
 * Outbound intent to an external system — not a domain event, not an async job envelope.
 * Idempotency: producer owns choosing a stable {@link idempotencyKey}.
 */
export type IntegrationCommand = {
  readonly kind: string;
  readonly payload: Readonly<Record<string, unknown>>;
  readonly correlation?: CorrelationContext;
  readonly idempotencyKey: string;
};
