/**
 * Versioned structured envelope for LLM JSON (or equivalent) — not Prisma models.
 */
export type StructuredAiEnvelope<TData extends Record<string, unknown>> = {
  readonly schemaId: string;
  readonly schemaVersion: string;
  readonly data: TData | null;
};

/**
 * Minimal assistant reply shape for validation / future persistence mapping.
 * (Not a DB row; not an FSM command.)
 */
export type AssistantReplyStructuredV1 = {
  replyText: string;
  refused: boolean;
  refusalReason?: string;
};

export const ASSISTANT_REPLY_SCHEMA_ID = 'salon.assistant_reply' as const;
export const ASSISTANT_REPLY_SCHEMA_VERSION = 'v1' as const;
