/**
 * Stable tool identifiers — not LLM-generated strings.
 */
export const SALES_TOOL_IDS = [
  'booking.create_request',
  'sales.escalation_handoff',
  'follow_up.schedule_contract',
] as const;

export type SalesToolId = (typeof SALES_TOOL_IDS)[number];

export type ToolIntentBase = {
  readonly intentId: string;
  readonly toolId: SalesToolId;
  readonly intentVersion: 'sales_tool_intent@v1';
  /** When true, executor must not mutate without matching confirmation. */
  readonly requiresConfirmation: boolean;
  readonly params: Readonly<Record<string, unknown>>;
};

export type BookingCreateRequestIntent = ToolIntentBase & {
  readonly toolId: 'booking.create_request';
};

export type EscalationHandoffIntent = ToolIntentBase & {
  readonly toolId: 'sales.escalation_handoff';
};

export type FollowUpScheduleContractIntent = ToolIntentBase & {
  readonly toolId: 'follow_up.schedule_contract';
};

export type SalesToolIntent =
  | BookingCreateRequestIntent
  | EscalationHandoffIntent
  | FollowUpScheduleContractIntent;
