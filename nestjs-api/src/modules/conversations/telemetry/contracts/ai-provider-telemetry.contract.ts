export type AiProviderOutcomeKind =
  | 'success'
  | 'refusal'
  | 'failure'
  | 'timeout'
  | 'not_invoked'
  | 'early_exit';

export type AiProviderTelemetryV1 = {
  readonly telemetryVersion: 'ai_provider_telemetry@v1';
  readonly outcome: AiProviderOutcomeKind;
  readonly wallClockMs?: number;
  readonly modelId?: string;
  readonly schemaId?: string;
  readonly schemaVersion?: string;
};
