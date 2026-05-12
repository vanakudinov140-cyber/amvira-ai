/**
 * Non-PII quality snapshot derived from {@link AiSalesDecisionEnvelope} when present.
 */
export type AiQualitySignalsV1 = {
  readonly qualityVersion: 'ai_quality_signals@v1';
  readonly overallConfidence?: number;
  readonly transitionConfidence?: number | null;
  readonly policyOutcome?: string;
  readonly objectionSeverity?: string;
  readonly objectionPrimaryCategory?: string | null;
  readonly bookingConversionLikelihood?: number;
};
