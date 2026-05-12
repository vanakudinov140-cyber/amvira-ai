/**
 * Correlation for telemetry only — mirrors inbound request identifiers.
 * Not a distributed trace implementation; compatible with future W3C traceparent injection.
 */
export type TelemetryCorrelationV1 = {
  readonly correlationVersion: 'telemetry_correlation@v1';
  readonly correlationId?: string;
  readonly dialogId: string;
  readonly turnIdempotencyKey?: string;
  /** Optional client- or edge-supplied trace id (opaque string). */
  readonly traceId?: string;
  readonly parentSpanId?: string;
};
