import type { AiSalesDecisionEnvelope } from '../../ai/sales-decisions/contracts/ai-sales-decision.contract';
import type { AssistantReplyQualityReportV1 } from '../../ai/quality/assistant-reply-quality.evaluator';
import type { OperatorAssistSignalsV1 } from './contracts/operator-assist.contract';

export function buildOperatorAssistSignals(input: {
  readonly decision: AiSalesDecisionEnvelope;
  readonly quality: AssistantReplyQualityReportV1;
  readonly userText: string;
}): OperatorAssistSignalsV1 {
  const warnings: string[] = [];
  if (input.quality.flags.length) {
    warnings.push(...input.quality.flags);
  }
  if (
    input.decision.confidence.overall <
    input.decision.objectionIntelligence.escalationThreshold
  ) {
    warnings.push('confidence_below_objection_threshold');
  }

  let urgency: OperatorAssistSignalsV1['escalationUrgency'] = 'low';
  if (input.decision.policyOutcome === 'escalate_human') {
    urgency = 'high';
  } else if (input.decision.objectionIntelligence.severity === 'high') {
    urgency = 'high';
  } else if (input.decision.objectionIntelligence.severity === 'medium') {
    urgency = 'medium';
  }

  let action: OperatorAssistSignalsV1['recommendedOperatorAction'] = 'monitor';
  if (urgency === 'high') {
    action = 'takeover_suggested';
  } else if (input.quality.overallQualityScore < 0.45) {
    action = 'reply_suggested';
  }
  if (input.decision.bookingConversion.nextBestAction === 'confirm_slot') {
    action = 'approve_booking';
  }

  const suggested =
    urgency === 'high'
      ? 'Подключитесь к диалогу: высокая эскалация или сильное возражение.'
      : input.quality.overallQualityScore < 0.45
        ? 'Можно уточнить одним коротким сообщением и предложить следующий конкретный шаг.'
        : 'Мониторинг без вмешательства.';

  return {
    assistVersion: 'operator_assist@v1',
    recommendedOperatorAction: action,
    suggestedManualReply: suggested,
    escalationUrgency: urgency,
    confidenceWarnings: warnings.slice(0, 8),
  };
}
