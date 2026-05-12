export type OperatorAssistSignalsV1 = Readonly<{
  readonly assistVersion: 'operator_assist@v1';
  readonly recommendedOperatorAction:
    | 'monitor'
    | 'reply_suggested'
    | 'takeover_suggested'
    | 'approve_booking'
    | 'none';
  readonly suggestedManualReply: string;
  readonly escalationUrgency: 'low' | 'medium' | 'high';
  readonly confidenceWarnings: readonly string[];
}>;
