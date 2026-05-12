import { Injectable } from '@nestjs/common';
import { isDialogStageCode } from '../../dialogs/domain/dialog-stage.types';
import type {
  AiSalesDecisionEnvelope,
  AiSalesDecisionInput,
} from './contracts/ai-sales-decision.contract';
import {
  extractSalesSignals,
  recommendStage,
} from './extraction/sales-signals.extractor';
import {
  buildBookingConversionOptimization,
  buildObjectionIntelligence,
} from './objection-intelligence.builder';
import { AiSalesDecisionPolicy } from './policies/ai-sales-decision.policy';

/**
 * Deterministic sales decisioning from user + assistant text. No LLM, no DB, no FSM writes.
 */
@Injectable()
export class AiSalesDecisionService {
  compose(input: AiSalesDecisionInput): AiSalesDecisionEnvelope {
    const policy = new AiSalesDecisionPolicy();
    const signals = extractSalesSignals(input);

    if (!isDialogStageCode(input.currentStage)) {
      const oi = buildObjectionIntelligence({
        objection: signals.objection,
        userText: input.userText,
        lead: signals.leadQualification,
        booking: signals.bookingReadiness,
      });
      const bc = buildBookingConversionOptimization({
        booking: signals.bookingReadiness,
        lead: signals.leadQualification,
        objection: signals.objection,
        intentsTopLabel: signals.intents[0]?.label ?? 'unknown',
      });
      return {
        version: 'sales_decision@v1',
        policyOutcome: 'suppress',
        confidence: { overall: signals.overallConfidence, transition: null },
        intents: signals.intents,
        objection: signals.objection,
        leadQualification: signals.leadQualification,
        bookingReadiness: signals.bookingReadiness,
        objectionIntelligence: oi,
        bookingConversion: bc,
        recommendedNextStage: null,
        transitionProposal: null,
        suppressedReason:
          input.dialogStatus === 'CLOSED'
            ? 'dialog_closed'
            : 'unknown_dialog_stage_code',
      };
    }

    const current = input.currentStage;
    const { recommended, proposal } = recommendStage(current, signals, policy);
    const hasLegalProposal = proposal !== null;
    const policyMeta = policy.evaluatePolicyOutcome({
      dialogStatus: input.dialogStatus,
      objection: signals.objection,
      overallConfidence: signals.overallConfidence,
      hasLegalProposal,
    });

    let transitionProposal = proposal;
    let recommendedNext = recommended;
    let transitionConfidence: number | null = proposal
      ? signals.overallConfidence
      : null;

    if (policyMeta.outcome === 'escalate_human' || policyMeta.outcome === 'suppress') {
      transitionProposal = null;
      recommendedNext = null;
      transitionConfidence = null;
    }

    const oi = buildObjectionIntelligence({
      objection: signals.objection,
      userText: input.userText,
      lead: signals.leadQualification,
      booking: signals.bookingReadiness,
    });
    const bc = buildBookingConversionOptimization({
      booking: signals.bookingReadiness,
      lead: signals.leadQualification,
      objection: signals.objection,
      intentsTopLabel: signals.intents[0]?.label ?? 'unknown',
    });

    return {
      version: 'sales_decision@v1',
      policyOutcome: policyMeta.outcome,
      confidence: {
        overall: signals.overallConfidence,
        transition: transitionConfidence,
      },
      intents: signals.intents,
      objection: signals.objection,
      leadQualification: signals.leadQualification,
      bookingReadiness: signals.bookingReadiness,
      objectionIntelligence: oi,
      bookingConversion: bc,
      recommendedNextStage: recommendedNext,
      transitionProposal,
      escalation: policyMeta.escalation,
      suppressedReason: policyMeta.suppressedReason,
    };
  }
}
