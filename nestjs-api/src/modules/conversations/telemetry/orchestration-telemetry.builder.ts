import type { UserMessageOrchestrationRequest } from '../contracts/user-message-orchestration.request';
import type { ConversationOrchestrationResult } from '../orchestration/conversation-orchestration.result';
import type { AiProviderTelemetryV1 } from './contracts/ai-provider-telemetry.contract';
import type { AiQualitySignalsV1 } from './contracts/ai-quality-signals.contract';
import type { DeliveryTelemetryV1 } from './contracts/delivery-telemetry.contract';
import type { EscalationTelemetryV1 } from './contracts/escalation-telemetry.contract';
import type { FunnelStageAnalyticsV1 } from './contracts/funnel-stage-analytics.contract';
import type { OperationalHealthSnapshotV1 } from './contracts/operational-health-snapshot.contract';
import type { OrchestrationTelemetrySnapshotV1 } from './contracts/orchestration-telemetry-snapshot.contract';
import type { SalesBehaviorTelemetryV1 } from './contracts/sales-behavior-telemetry.contract';
import type { OrchestrationTimingV1 } from './contracts/orchestration-timing.contract';
import type {
  FailureTelemetryBucket,
  RetryFailureAnalyticsV1,
} from './contracts/retry-failure-analytics.contract';
import type { TelemetryCorrelationV1 } from './contracts/telemetry-correlation.contract';
import type { TelemetryStructuredEventV1 } from './contracts/telemetry-structured-event.contract';
import type {
  ToolExecutionTelemetryV1,
  YclientsToolTelemetryV1,
} from './contracts/tool-execution-telemetry.contract';
import {
  mapOrchestrationStatusToAnalyticsOutcome,
} from './contracts/conversation-outcome.taxonomy';

export type OrchestrationTelemetryBuilderInput = {
  readonly request: UserMessageOrchestrationRequest;
  readonly dialog?: {
    readonly currentStage: string;
    readonly status: string;
    readonly channel: string;
  };
  readonly result: ConversationOrchestrationResult;
  readonly timing: OrchestrationTimingV1;
  readonly executeToolsRequested: boolean;
};

function buildCorrelation(
  request: UserMessageOrchestrationRequest,
): TelemetryCorrelationV1 {
  return {
    correlationVersion: 'telemetry_correlation@v1',
    correlationId: request.correlationId,
    dialogId: request.dialogId,
    turnIdempotencyKey: request.turnIdempotencyKey,
    traceId: request.telemetryContext?.traceId,
    parentSpanId: request.telemetryContext?.parentSpanId,
  };
}

function failureBucketFromResult(
  result: ConversationOrchestrationResult,
): FailureTelemetryBucket {
  switch (result.status) {
    case 'partial_ai_timeout':
      return 'ai_timeout';
    case 'partial_ai_refused':
      return 'ai_refusal';
    case 'partial_ai_failed': {
      const reason = result.aiRefusal?.reason ?? '';
      if (reason === 'ai.timeout') {
        return 'ai_timeout';
      }
      if (reason === 'validation.failed' || reason.startsWith('validation.')) {
        return 'ai_validation';
      }
      return 'ai_provider';
    }
    case 'failed_user_message_persist':
      return 'user_persist';
    case 'blocked_dialog':
    case 'blocked_dialog_not_found':
      return 'blocked_dialog';
    case 'completed_with_delivery_warning':
      return 'delivery';
    default:
      return 'none';
  }
}

function buildRetryFailure(
  result: ConversationOrchestrationResult,
): RetryFailureAnalyticsV1 {
  return {
    analyticsVersion: 'retry_failure_analytics@v1',
    recoverability: result.recoverability,
    failureBucket: failureBucketFromResult(result),
    aiRefusalReason: result.aiRefusal?.reason,
  };
}

function buildAiProvider(
  result: ConversationOrchestrationResult,
  timing: OrchestrationTimingV1,
): AiProviderTelemetryV1 | undefined {
  const wall = timing.aiSuggestWallMs;
  if (result.candidate) {
    return {
      telemetryVersion: 'ai_provider_telemetry@v1',
      outcome: 'success',
      wallClockMs: wall,
      modelId: result.candidate.modelId,
      schemaId: result.candidate.schemaId,
      schemaVersion: result.candidate.schemaVersion,
    };
  }
  if (result.status === 'partial_ai_timeout') {
    return {
      telemetryVersion: 'ai_provider_telemetry@v1',
      outcome: 'timeout',
      wallClockMs: wall,
    };
  }
  if (result.status === 'partial_ai_refused') {
    return {
      telemetryVersion: 'ai_provider_telemetry@v1',
      outcome: 'refusal',
      wallClockMs: wall,
    };
  }
  if (result.status === 'partial_ai_failed') {
    return {
      telemetryVersion: 'ai_provider_telemetry@v1',
      outcome: 'failure',
      wallClockMs: wall,
    };
  }
  if (
    result.status === 'blocked_dialog' ||
    result.status === 'blocked_dialog_not_found' ||
    result.status === 'failed_user_message_persist'
  ) {
    return {
      telemetryVersion: 'ai_provider_telemetry@v1',
      outcome: 'not_invoked',
    };
  }
  return undefined;
}

function buildAiQuality(
  result: ConversationOrchestrationResult,
): AiQualitySignalsV1 | undefined {
  const d = result.aiSalesDecision;
  if (!d) {
    return undefined;
  }
  return {
    qualityVersion: 'ai_quality_signals@v1',
    overallConfidence: d.confidence.overall,
    transitionConfidence: d.confidence.transition,
    policyOutcome: d.policyOutcome,
    objectionSeverity: d.objection.severity,
    objectionPrimaryCategory: d.objectionIntelligence.primaryCategory,
    bookingConversionLikelihood: d.bookingConversion.conversionLikelihood,
  };
}

function buildTools(
  result: ConversationOrchestrationResult,
  executeToolsRequested: boolean,
): ToolExecutionTelemetryV1 {
  const proposals = result.toolProposals ?? [];
  const batch = result.toolExecution;
  if (!executeToolsRequested || !batch) {
    return {
      telemetryVersion: 'tool_execution_telemetry@v1',
      executed: false,
      proposalCount: proposals.length,
      successCount: 0,
      skippedCount: 0,
      failedCount: 0,
    };
  }
  let successCount = 0;
  let skippedCount = 0;
  let failedCount = 0;
  for (const it of batch.items) {
    if (it.kind === 'success') {
      successCount += 1;
    } else if (it.kind === 'skipped') {
      skippedCount += 1;
    } else {
      failedCount += 1;
    }
  }
  return {
    telemetryVersion: 'tool_execution_telemetry@v1',
    executed: true,
    proposalCount: proposals.length,
    successCount,
    skippedCount,
    failedCount,
    yclients: buildYclientsTelemetryFromToolBatch(batch),
  };
}

function buildYclientsTelemetryFromToolBatch(
  batch: ConversationOrchestrationResult['toolExecution'],
): YclientsToolTelemetryV1 | undefined {
  if (!batch) {
    return undefined;
  }
  let yclientsRequestMs = 0;
  let syncOutcome: YclientsToolTelemetryV1['syncOutcome'] | undefined;
  let providerStatus: string | undefined;
  let availabilityFreshness: string | undefined;
  for (const it of batch.items) {
    const y = it.payload?.yclients as YclientsToolTelemetryV1 | undefined;
    if (!y) {
      continue;
    }
    if (typeof y.yclientsRequestMs === 'number') {
      yclientsRequestMs += y.yclientsRequestMs;
    }
    if (y.syncOutcome) {
      syncOutcome = y.syncOutcome;
    }
    if (y.providerStatus) {
      providerStatus = y.providerStatus;
    }
    if (y.availabilityFreshness) {
      availabilityFreshness = y.availabilityFreshness;
    }
  }
  if (
    yclientsRequestMs === 0 &&
    !syncOutcome &&
    !providerStatus &&
    !availabilityFreshness
  ) {
    return undefined;
  }
  return {
    yclientsRequestMs: yclientsRequestMs > 0 ? yclientsRequestMs : undefined,
    syncOutcome,
    providerStatus,
    availabilityFreshness,
  };
}

function buildDelivery(
  result: ConversationOrchestrationResult,
): DeliveryTelemetryV1 | undefined {
  const d = result.deliveryOutcome;
  if (!d) {
    return undefined;
  }
  if (d.kind === 'sync_delivered') {
    return {
      telemetryVersion: 'delivery_telemetry@v1',
      outcomeKind: d.kind,
      syncReceiptStatus: d.receipt.status,
    };
  }
  if (d.kind === 'async_enqueued') {
    return {
      telemetryVersion: 'delivery_telemetry@v1',
      outcomeKind: d.kind,
      asyncAccepted: d.dispatch.accepted,
    };
  }
  return {
    telemetryVersion: 'delivery_telemetry@v1',
    outcomeKind: d.kind,
  };
}

function buildEscalation(
  result: ConversationOrchestrationResult,
): EscalationTelemetryV1 | undefined {
  const env = result.operationsEnvelope;
  if (!env) {
    return undefined;
  }
  return {
    telemetryVersion: 'escalation_telemetry@v1',
    hasEscalationIntent: env.escalationIntent != null,
    queueRoutingConfirmed: env.handoffDecision?.routeToOperatorQueue === true,
    suggestedReasonCode: env.escalationIntent?.suggestedReasonCode,
    interventionClassification: env.intervention.classification,
  };
}

function buildHealth(
  result: ConversationOrchestrationResult,
  tools: ToolExecutionTelemetryV1,
): OperationalHealthSnapshotV1 {
  const delivery = result.deliveryOutcome;
  const deliveryAttempted =
    delivery != null && delivery.kind !== 'skipped';
  const deliverySucceeded =
    delivery?.kind === 'sync_delivered'
      ? delivery.receipt.status !== 'failed'
      : delivery?.kind === 'async_enqueued'
        ? delivery.dispatch.accepted === true
        : false;
  const toolsExecutedCleanly =
    !tools.executed || tools.failedCount === 0;
  return {
    healthVersion: 'operational_health@v1',
    turnCompleted: result.status === 'completed',
    turnCompletedWithWarnings:
      result.status === 'completed_with_assistant_persist_warning' ||
      result.status === 'completed_with_delivery_warning',
    aiCandidateProduced: result.candidate != null,
    toolsExecutedCleanly,
    deliveryAttempted,
    deliverySucceeded,
  };
}

function buildSalesBehavior(
  result: ConversationOrchestrationResult,
): SalesBehaviorTelemetryV1 | undefined {
  const d = result.aiSalesDecision;
  if (!d) {
    return undefined;
  }
  const bookingProposalCount =
    result.toolProposals?.filter(
      (p) => p.intent.toolId === 'booking.create_request',
    ).length ?? 0;
  return {
    telemetryVersion: 'sales_behavior@v1',
    objectionPrimary: d.objectionIntelligence.primaryCategory,
    bookingProposalCount,
    bookingConversionLikelihood: d.bookingConversion.conversionLikelihood,
    aiRecoveryUsedFallback: result.aiReplyMeta?.usedFallback === true,
    assistantQualityOverall: result.assistantReplyQuality?.overallQualityScore,
    escalationSuggested: result.operationsEnvelope?.escalationIntent != null,
  };
}

export function buildOrchestrationTelemetrySnapshot(
  input: OrchestrationTelemetryBuilderInput,
): OrchestrationTelemetrySnapshotV1 {
  const funnel: FunnelStageAnalyticsV1 | undefined = input.dialog
    ? {
        funnelVersion: 'funnel_stage_analytics@v1',
        dialogStageCode: input.dialog.currentStage,
        dialogStatus: input.dialog.status,
        channel: input.dialog.channel,
      }
    : undefined;
  const tools = buildTools(input.result, input.executeToolsRequested);
  return {
    snapshotVersion: 'orchestration_telemetry_snapshot@v1',
    outcome: mapOrchestrationStatusToAnalyticsOutcome(input.result.status),
    orchestrationStatus: input.result.status,
    timing: input.timing,
    correlation: buildCorrelation(input.request),
    funnel,
    aiProvider: buildAiProvider(input.result, input.timing),
    aiQuality: buildAiQuality(input.result),
    tools,
    delivery: buildDelivery(input.result),
    escalation: buildEscalation(input.result),
    retryFailure: buildRetryFailure(input.result),
    health: buildHealth(input.result, tools),
    salesBehavior: buildSalesBehavior(input.result),
  };
}

export function buildOrchestrationTelemetryStructuredEvent(
  eventKind: TelemetryStructuredEventV1['eventKind'],
  payload: OrchestrationTelemetrySnapshotV1,
): TelemetryStructuredEventV1 {
  return {
    eventFamily: 'telemetry',
    eventKind,
    schemaVersion: 'telemetry_structured@v1',
    emittedAt: new Date().toISOString(),
    payload,
  };
}
