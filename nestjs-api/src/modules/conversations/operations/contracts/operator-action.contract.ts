/**
 * Explicit operator intents — execution belongs to future application services, not AI.
 */
export const OPERATOR_ACTION_KINDS = [
  'takeover.begin',
  'takeover.release',
  'booking.approve_manual',
  'booking.reject_manual',
  'notes.append',
  'conversation.resume_assistant',
] as const;

export type OperatorActionKind = (typeof OPERATOR_ACTION_KINDS)[number];

export type OperatorActionRequestV1 = {
  readonly actionVersion: 'operator_action@v1';
  readonly kind: OperatorActionKind;
  readonly dialogId: string;
  readonly correlationId?: string;
  readonly payload: Readonly<Record<string, unknown>>;
};
