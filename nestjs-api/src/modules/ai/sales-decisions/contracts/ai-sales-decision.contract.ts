import type { DialogStageCode } from '../../../dialogs/domain/dialog-stage.types';

/**
 * AI sales decisioning — proposals only. FSM applies or rejects transitions elsewhere.
 */
export type AiSalesIntentLabel =
  | 'informational'
  | 'objection'
  | 'booking_interest'
  | 'qualification'
  | 'smalltalk'
  | 'unknown';

export type AiSalesIntentSignal = {
  readonly label: AiSalesIntentLabel;
  readonly score: number;
};

export type AiSalesObjectionProfile = {
  readonly detected: boolean;
  readonly severity: 'none' | 'low' | 'medium' | 'high';
  readonly signals: readonly string[];
};

export type ObjectionCategory =
  | 'price'
  | 'trust'
  | 'timing'
  | 'hesitation'
  | 'comparison'
  | 'no_response'
  | 'unclear_need';

export type ObjectionRecoveryStrategy =
  | 'empathy_clarify'
  | 'reframe_value'
  | 'reduce_commitment'
  | 'social_proof_light'
  | 'pace_control'
  | 'human_handoff_prep';

export type ObjectionIntelligenceV1 = Readonly<{
  readonly version: 'objection_intelligence@v1';
  readonly primaryCategory: ObjectionCategory | null;
  readonly secondaryCategories: readonly ObjectionCategory[];
  readonly severity: AiSalesObjectionProfile['severity'];
  readonly recoveryStrategy: ObjectionRecoveryStrategy;
  /** When confidence / momentum falls below this band, suggest human assist. */
  readonly escalationThreshold: number;
}>;

export type BookingConversionOptimizationV1 = Readonly<{
  readonly version: 'booking_conversion@v1';
  readonly nextBestAction:
    | 'clarify_service'
    | 'confirm_slot'
    | 'collect_contact'
    | 'handle_objection'
    | 'soft_nudge'
    | 'hold';
  readonly bookingMomentumScore: number;
  readonly leadTemperature: 'cold' | 'warm' | 'hot';
  readonly conversionLikelihood: number;
}>;

export type AiSalesLeadQualification = {
  readonly level: 'cold' | 'warm' | 'hot';
  readonly score: number;
  readonly signals: readonly string[];
};

export type AiSalesBookingReadiness = {
  readonly ready: boolean;
  readonly score: number;
  readonly signals: readonly string[];
};

export type AiSalesTransitionProposal = {
  readonly fromStage: DialogStageCode;
  readonly toStage: DialogStageCode;
  readonly rationale: string;
};

export type AiSalesDecisionConfidence = {
  /** Combined extractor confidence [0,1]. */
  readonly overall: number;
  /** Confidence that {@link AiSalesTransitionProposal} is appropriate [0,1] or null if no proposal. */
  readonly transition: number | null;
};

export type AiSalesDecisionPolicyOutcome =
  | 'propose'
  | 'suppress'
  | 'escalate_human';

/**
 * Attached to conversation orchestration result — never mutates dialog rows.
 */
export type AiSalesDecisionEnvelope = {
  readonly version: 'sales_decision@v1';
  readonly policyOutcome: AiSalesDecisionPolicyOutcome;
  readonly confidence: AiSalesDecisionConfidence;
  readonly intents: readonly AiSalesIntentSignal[];
  readonly objection: AiSalesObjectionProfile;
  readonly leadQualification: AiSalesLeadQualification;
  readonly bookingReadiness: AiSalesBookingReadiness;
  readonly objectionIntelligence: ObjectionIntelligenceV1;
  readonly bookingConversion: BookingConversionOptimizationV1;
  /** Suggested funnel position — FSM may ignore or reject. */
  readonly recommendedNextStage: DialogStageCode | null;
  /** FSM-safe single-hop proposal, or null when suppressed / escalated / illegal. */
  readonly transitionProposal: AiSalesTransitionProposal | null;
  readonly escalation?: Readonly<{ readonly reason: string }>;
  readonly suppressedReason?: string;
};

export type AiSalesDecisionInput = {
  readonly userText: string;
  readonly assistantReplyText: string;
  readonly currentStage: string;
  readonly dialogStatus: string;
};
