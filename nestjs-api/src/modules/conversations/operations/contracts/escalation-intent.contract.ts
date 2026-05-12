import type { EscalationReasonCode } from './escalation-reasons.taxonomy';

/**
 * AI / confidence layer may emit escalation *intent* only — never queue placement or takeover.
 */
export type EscalationIntentV1 = {
  readonly intentVersion: 'escalation_intent@v1';
  readonly dialogId: string;
  readonly composedAt: string;
  readonly suggestedReasonCode: EscalationReasonCode;
  readonly signals: {
    readonly salesPolicyEscalateHuman: boolean;
    readonly confidenceSuggestsQueue: boolean;
    readonly bookingRequiresManualApproval: boolean;
  };
};
