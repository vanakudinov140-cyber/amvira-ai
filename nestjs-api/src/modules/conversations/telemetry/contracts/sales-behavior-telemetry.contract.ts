export type SalesBehaviorTelemetryV1 = Readonly<{
  readonly telemetryVersion: 'sales_behavior@v1';
  readonly objectionPrimary?: string | null;
  readonly bookingProposalCount: number;
  readonly bookingConversionLikelihood?: number;
  readonly aiRecoveryUsedFallback: boolean;
  readonly assistantQualityOverall?: number;
  readonly escalationSuggested: boolean;
}>;
