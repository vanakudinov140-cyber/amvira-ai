import type { OrchestrationTelemetrySnapshotV1 } from './orchestration-telemetry-snapshot.contract';

export type TelemetryStructuredEventKind =
  | 'orchestration.turn_snapshot'
  | 'orchestration.idempotency_hit';

/**
 * Structured operational telemetry line — distinct from the domain application event bus.
 */
export type TelemetryStructuredEventV1 = {
  readonly eventFamily: 'telemetry';
  readonly eventKind: TelemetryStructuredEventKind;
  readonly schemaVersion: 'telemetry_structured@v1';
  readonly emittedAt: string;
  readonly payload: OrchestrationTelemetrySnapshotV1;
};
