export type YclientsToolTelemetryV1 = Readonly<{
  readonly yclientsRequestMs?: number;
  readonly syncOutcome?: 'synced' | 'failed' | 'skipped' | 'not_attempted';
  readonly providerStatus?: string;
  readonly availabilityFreshness?: string;
}>;

export type ToolExecutionTelemetryV1 = {
  readonly telemetryVersion: 'tool_execution_telemetry@v1';
  readonly executed: boolean;
  readonly proposalCount: number;
  readonly successCount: number;
  readonly skippedCount: number;
  readonly failedCount: number;
  /** Populated when booking / YCLIENTS tools attach integration metrics to payloads. */
  readonly yclients?: YclientsToolTelemetryV1;
};
