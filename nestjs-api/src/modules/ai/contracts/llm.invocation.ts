export type LlmMessageRole = 'system' | 'user' | 'assistant';

export type LlmChatMessage = {
  readonly role: LlmMessageRole;
  readonly content: string;
};

/**
 * Provider-neutral invocation — future GigaChat adapter maps this to HTTP/SDK.
 */
export type LlmInvocationRequest = {
  readonly messages: readonly LlmChatMessage[];
  readonly temperature?: number;
  readonly maxTokens?: number;
  readonly correlationId?: string;
};

export type LlmInvocationResponse = {
  readonly rawText: string;
  readonly finishReason?: string;
};
