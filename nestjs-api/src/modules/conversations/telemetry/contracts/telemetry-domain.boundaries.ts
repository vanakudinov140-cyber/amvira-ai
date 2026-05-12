/**
 * Domain boundaries (documentation-only constants):
 *
 * - **Business events**: persisted / published via the application event publisher (dialog created,
 *   stage transitioned, etc.). Consumers drive workflows and projections.
 *
 * - **Telemetry events**: this module’s `TelemetryStructuredEventV1` — operational metrics,
 *   latency, outcomes. Fire-and-forget; must never throw into the request path.
 *
 * - **Audit events**: operator / compliance trail (see `operations/contracts/audit-trail.contract.ts`).
 *   Immutable human-action records; not aggregated as time-series metrics.
 *
 * - **Analytics**: derived labels in contracts (outcome taxonomy, funnel snapshot, failure buckets).
 *   Same transport as telemetry here; downstream ETL may split streams by `eventFamily`.
 */
export const TELEMETRY_EVENT_FAMILY = 'telemetry' as const;
