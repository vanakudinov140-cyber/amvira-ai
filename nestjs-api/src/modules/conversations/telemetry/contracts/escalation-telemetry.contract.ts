export type EscalationTelemetryV1 = {
  readonly telemetryVersion: 'escalation_telemetry@v1';
  readonly hasEscalationIntent: boolean;
  readonly queueRoutingConfirmed: boolean;
  readonly suggestedReasonCode?: string;
  readonly interventionClassification?: string;
};
