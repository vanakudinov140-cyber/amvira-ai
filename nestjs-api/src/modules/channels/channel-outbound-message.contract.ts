import type { CorrelationContext } from '../../shared/correlation/correlation-context.contract';

export type ChannelOutboundMessage = {
  readonly body: string;
  readonly metadata?: Readonly<Record<string, unknown>>;
  readonly correlation?: CorrelationContext;
  readonly idempotencyKey: string;
};
