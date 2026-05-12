import { Injectable } from '@nestjs/common';
import type { AiSalesDecisionEnvelope } from '../../../ai/sales-decisions/contracts/ai-sales-decision.contract';
import type { SalesToolIntent } from '../contracts/tool-intent.contract';
import type {
  SalesToolProposal,
  ToolProposalValidation,
} from '../contracts/tool-execution.contract';
import { isToolEligibleForStage } from '../policies/tool-eligibility.policy';

export type SalesToolProposalInput = {
  readonly dialogId: string;
  readonly channel: string;
  readonly currentStage: string;
  readonly decision: AiSalesDecisionEnvelope;
};

@Injectable()
export class SalesToolProposalBuilder {
  build(input: SalesToolProposalInput): readonly SalesToolProposal[] {
    const out: SalesToolProposal[] = [];
    let n = 0;
    const nextId = (tool: string) => `intent:${input.dialogId}:${tool}:${n++}`;

    const d = input.decision;

    if (d.policyOutcome === 'escalate_human') {
      const intentId = nextId('escalation');
      const intent: SalesToolIntent = {
        intentId,
        toolId: 'sales.escalation_handoff',
        intentVersion: 'sales_tool_intent@v1',
        requiresConfirmation: false,
        params: {
          reason: d.escalation?.reason ?? 'unspecified',
          dialogId: input.dialogId,
        },
      };
      out.push({
        proposalId: intentId,
        intent,
        validation: this.validate(intent, input.currentStage),
      });
    }

    if (
      d.policyOutcome === 'propose' &&
      d.transitionProposal?.toStage === 'BOOKING'
    ) {
      const intentId = nextId('booking');
      const intent: SalesToolIntent = {
        intentId,
        toolId: 'booking.create_request',
        intentVersion: 'sales_tool_intent@v1',
        requiresConfirmation: true,
        params: {
          dialogId: input.dialogId,
          rationale: d.transitionProposal.rationale,
        },
      };
      out.push({
        proposalId: intentId,
        intent,
        validation: this.validate(intent, d.transitionProposal.fromStage),
      });
    }

    if (
      d.bookingReadiness.ready &&
      d.policyOutcome === 'propose' &&
      d.transitionProposal?.toStage !== 'BOOKING'
    ) {
      const intentId = nextId('followup');
      const intent: SalesToolIntent = {
        intentId,
        toolId: 'follow_up.schedule_contract',
        intentVersion: 'sales_tool_intent@v1',
        requiresConfirmation: true,
        params: {
          dialogId: input.dialogId,
          channel: input.channel,
          readinessScore: d.bookingReadiness.score,
        },
      };
      out.push({
        proposalId: intentId,
        intent,
        validation: this.validate(intent, input.currentStage),
      });
    }

    return out;
  }

  private validate(
    intent: SalesToolIntent,
    stageForEligibility: string,
  ): ToolProposalValidation {
    if (!isToolEligibleForStage(intent.toolId, stageForEligibility)) {
      return {
        ok: false,
        reason: `tool_not_eligible_for_stage:${intent.toolId}:${stageForEligibility}`,
      };
    }
    return { ok: true };
  }
}
