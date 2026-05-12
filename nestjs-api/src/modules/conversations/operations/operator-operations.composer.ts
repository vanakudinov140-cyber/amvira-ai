import { Injectable } from '@nestjs/common';
import type { AssistantReplyQualityReportV1 } from '../../ai/quality/assistant-reply-quality.evaluator';
import type { AiSalesDecisionEnvelope } from '../../ai/sales-decisions/contracts/ai-sales-decision.contract';
import type { EscalationReasonCode } from './contracts/escalation-reasons.taxonomy';
import type { SalesToolProposal } from '../tooling/contracts/tool-execution.contract';
import type { AuditTrailEntryV1 } from './contracts/audit-trail.contract';
import type { EscalationIntentV1 } from './contracts/escalation-intent.contract';
import type { EscalationQueueItemV1 } from './contracts/escalation-queue.contract';
import type { HumanHandoffDecisionV1 } from './contracts/human-handoff-decision.contract';
import type { InterventionResultV1 } from './contracts/intervention-result.contract';
import type { OperationsEnvelopeV1 } from './contracts/operations-envelope.contract';
import type { TakeoverStateV1 } from './contracts/takeover.contract';
import { buildOperatorAssistSignals } from './operator-assist.builder';
import { buildAiConfidenceRouting } from './policies/ai-confidence-routing.policy';
import { buildTakeoverEligibility } from './policies/takeover-eligibility.policy';

export type OperatorOperationsComposerInput = {
  readonly dialogId: string;
  readonly correlationId?: string;
  readonly dialogStatus: string;
  readonly decision: AiSalesDecisionEnvelope;
  readonly toolProposals: readonly SalesToolProposal[];
  readonly operatorTakeoverActive: boolean;
  readonly resumeAssistantRequested: boolean;
  readonly confirmEscalationToQueue: boolean;
  readonly assistantReplyQuality?: AssistantReplyQualityReportV1;
  readonly userTextForAssist?: string;
};

function pickEscalationReasonCode(input: {
  readonly decision: AiSalesDecisionEnvelope;
  readonly bookingRequiresManualApproval: boolean;
  readonly confidenceSuggestsQueue: boolean;
}): EscalationReasonCode {
  if (input.bookingRequiresManualApproval) {
    return 'booking_manual_review_required';
  }
  if (input.decision.policyOutcome === 'escalate_human') {
    return 'high_objection_low_confidence';
  }
  if (input.confidenceSuggestsQueue) {
    return 'unspecified';
  }
  return 'operator_requested';
}

@Injectable()
export class OperatorOperationsComposer {
  compose(input: OperatorOperationsComposerInput): OperationsEnvelopeV1 {
    const now = new Date().toISOString();
    const routing = buildAiConfidenceRouting(input.decision);
    const takeoverEligibility = buildTakeoverEligibility({
      decision: input.decision,
      operatorTakeoverActive: input.operatorTakeoverActive,
    });

    const bookingRequiresManualApproval = input.toolProposals.some(
      (p) =>
        p.intent.toolId === 'booking.create_request' &&
        p.validation.ok &&
        p.intent.requiresConfirmation,
    );

    const salesPolicyEscalateHuman =
      input.decision.policyOutcome === 'escalate_human';
    const confidenceSuggestsQueue = routing.suggestQueueEscalation;

    const hasEscalationIntent =
      salesPolicyEscalateHuman ||
      confidenceSuggestsQueue ||
      bookingRequiresManualApproval;

    const suggestedReasonCode = pickEscalationReasonCode({
      decision: input.decision,
      bookingRequiresManualApproval,
      confidenceSuggestsQueue,
    });

    const escalationIntent: EscalationIntentV1 | undefined = hasEscalationIntent
      ? {
          intentVersion: 'escalation_intent@v1',
          dialogId: input.dialogId,
          composedAt: now,
          suggestedReasonCode,
          signals: {
            salesPolicyEscalateHuman,
            confidenceSuggestsQueue,
            bookingRequiresManualApproval,
          },
        }
      : undefined;

    const takeoverState: TakeoverStateV1 = {
      takeoverVersion: 'takeover_state@v1',
      dialogId: input.dialogId,
      suspension: input.operatorTakeoverActive
        ? 'operator_takeover_active'
        : takeoverEligibility.suggestedSuspension === 'suggested_hold'
          ? 'suggested_hold'
          : 'none',
      ownership: input.operatorTakeoverActive ? 'operator_primary' : 'assistant_primary',
      assistantOutboundHold: input.operatorTakeoverActive,
    };

    const routeToQueue = input.confirmEscalationToQueue === true;

    const handoffReason: EscalationReasonCode = routeToQueue
      ? escalationIntent?.suggestedReasonCode ?? 'operator_requested'
      : suggestedReasonCode;

    const handoff: HumanHandoffDecisionV1 | undefined = routeToQueue
      ? {
          decisionVersion: 'human_handoff@v1',
          dialogId: input.dialogId,
          decidedAt: now,
          routeToOperatorQueue: true,
          reasonCode: handoffReason,
          recoverability: 'recoverable',
        }
      : undefined;

    const escalationQueueItem: EscalationQueueItemV1 | undefined = routeToQueue
      ? {
          itemVersion: 'escalation_queue_item@v1',
          dialogId: input.dialogId,
          correlationId: input.correlationId,
          reasonCode: handoffReason,
          priority:
            input.decision.policyOutcome === 'escalate_human' ? 'high' : 'medium',
          enqueuedAt: now,
          payload: {
            source: 'operations_envelope',
            confidence: routing.overallConfidence,
            dialogStatus: input.dialogStatus,
          },
        }
      : undefined;

    const manualBookingApproval = bookingRequiresManualApproval
      ? {
          flowVersion: 'manual_booking_approval@v1' as const,
          dialogId: input.dialogId,
          state: 'pending_operator' as const,
          reason: 'confirmation_required_for_booking_tool',
        }
      : undefined;

    const audit: AuditTrailEntryV1[] = [
      {
        entryVersion: 'audit_trail@v1',
        at: now,
        actor: 'ai_sales_decision',
        event: 'sales_decision_composed',
        detail: {
          policyOutcome: input.decision.policyOutcome,
          overallConfidence: input.decision.confidence.overall,
        },
      },
      {
        entryVersion: 'audit_trail@v1',
        at: now,
        actor: 'system',
        event: 'tool_proposals_materialized',
        detail: { count: input.toolProposals.length },
      },
    ];

    if (input.resumeAssistantRequested) {
      audit.push({
        entryVersion: 'audit_trail@v1',
        at: now,
        actor: 'operator',
        event: 'resume_assistant_requested',
        detail: { dialogId: input.dialogId },
      });
    }

    if (routeToQueue) {
      audit.push({
        entryVersion: 'audit_trail@v1',
        at: now,
        actor: 'operator',
        event: 'escalation_queue_routing_confirmed',
        detail: { dialogId: input.dialogId, reasonCode: handoffReason },
      });
    }

    let classification: InterventionResultV1['classification'] = 'no_intervention';

    if (input.resumeAssistantRequested && !input.operatorTakeoverActive) {
      classification = 'resume_pending';
    } else if (input.operatorTakeoverActive) {
      classification = 'takeover_active';
    } else if (routeToQueue) {
      classification = 'escalation_routed';
    } else if (escalationIntent) {
      classification = 'escalation_suggested';
    } else if (
      takeoverEligibility.takeoverAllowed &&
      takeoverEligibility.suggestedSuspension === 'suggested_hold'
    ) {
      classification = 'takeover_suggested';
    }

    const intervention: InterventionResultV1 = {
      resultVersion: 'intervention_result@v1',
      dialogId: input.dialogId,
      classification,
      handoff,
      takeover: takeoverState,
      audit,
    };

    const defaultQuality: AssistantReplyQualityReportV1 = {
      reportVersion: 'assistant_reply_quality@v1',
      verbosityScore: 0.5,
      repetitionScore: 0.1,
      bookingCtaScore: 0.3,
      hallucinationRiskScore: 0.1,
      toneConsistencyScore: 0.5,
      escalationAppropriateScore: 0.5,
      compactnessScore: 0.5,
      overallQualityScore: 0.5,
      flags: ['quality_not_evaluated'],
    };

    const operatorAssist = buildOperatorAssistSignals({
      decision: input.decision,
      quality: input.assistantReplyQuality ?? defaultQuality,
      userText: input.userTextForAssist ?? '',
    });

    return {
      envelopeVersion: 'operations@v1',
      dialogId: input.dialogId,
      composedAt: now,
      routing,
      takeoverEligibility,
      takeoverState,
      escalationIntent,
      handoffDecision: handoff,
      escalationQueueItem,
      manualBookingApproval,
      intervention,
      operatorAssist,
    };
  }
}
