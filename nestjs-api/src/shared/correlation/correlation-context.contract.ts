/**
 * Cross-layer correlation — no OTEL/HTTP dependency.
 * Propagation: HTTP middleware → application services → events/jobs/commands (optional fields).
 */
export type CorrelationContext = {
  readonly correlationId: string;
  readonly causationId?: string;
  readonly traceparent?: string;
};
