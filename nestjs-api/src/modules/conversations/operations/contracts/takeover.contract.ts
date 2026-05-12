/**
 * Takeover is owned by humans / explicit operator actions — never auto-cleared by AI.
 */
export type AssistantSuspensionMode =
  | 'none'
  | 'suggested_hold'
  | 'operator_takeover_active';

export type ConversationOwnershipMode =
  | 'assistant_primary'
  | 'shared'
  | 'operator_primary';

export type TakeoverStateV1 = {
  readonly takeoverVersion: 'takeover_state@v1';
  readonly dialogId: string;
  readonly suspension: AssistantSuspensionMode;
  readonly ownership: ConversationOwnershipMode;
  /** When true, outbound assistant generation should be skipped by orchestration policy (caller-enforced). */
  readonly assistantOutboundHold: boolean;
};
