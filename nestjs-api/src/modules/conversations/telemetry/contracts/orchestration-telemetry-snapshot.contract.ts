import type { AiProviderTelemetryV1 } from './ai-provider-telemetry.contract';
import type { AiQualitySignalsV1 } from './ai-quality-signals.contract';
import type { ConversationAnalyticsOutcome } from './conversation-outcome.taxonomy';
import type { DeliveryTelemetryV1 } from './delivery-telemetry.contract';
import type { EscalationTelemetryV1 } from './escalation-telemetry.contract';
import type { FunnelStageAnalyticsV1 } from './funnel-stage-analytics.contract';
import type { OperationalHealthSnapshotV1 } from './operational-health-snapshot.contract';
import type { OrchestrationTimingV1 } from './orchestration-timing.contract';
import type { RetryFailureAnalyticsV1 } from './retry-failure-analytics.contract';
import type { TelemetryCorrelationV1 } from './telemetry-correlation.contract';
import type { ToolExecutionTelemetryV1 } from './tool-execution-telemetry.contract';
import type { SalesBehaviorTelemetryV1 } from './sales-behavior-telemetry.contract';

export type OrchestrationTelemetrySnapshotV1 = {
  readonly snapshotVersion: 'orchestration_telemetry_snapshot@v1';
  readonly outcome: ConversationAnalyticsOutcome;
  readonly orchestrationStatus: string;
  readonly timing: OrchestrationTimingV1;
  readonly correlation: TelemetryCorrelationV1;
  readonly funnel?: FunnelStageAnalyticsV1;
  readonly aiProvider?: AiProviderTelemetryV1;
  readonly aiQuality?: AiQualitySignalsV1;
  readonly tools?: ToolExecutionTelemetryV1;
  readonly delivery?: DeliveryTelemetryV1;
  readonly escalation?: EscalationTelemetryV1;
  readonly retryFailure: RetryFailureAnalyticsV1;
  readonly health: OperationalHealthSnapshotV1;
  readonly salesBehavior?: SalesBehaviorTelemetryV1;
};
