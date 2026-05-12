export type FailureTelemetryBucket =
  | 'none'
  | 'ai_timeout'
  | 'ai_provider'
  | 'ai_validation'
  | 'ai_refusal'
  | 'user_persist'
  | 'blocked_dialog'
  | 'delivery'
  | 'unknown';

export type RetryFailureAnalyticsV1 = {
  readonly analyticsVersion: 'retry_failure_analytics@v1';
  readonly recoverability?: 'recoverable' | 'non_recoverable';
  readonly failureBucket: FailureTelemetryBucket;
  readonly aiRefusalReason?: string;
};
