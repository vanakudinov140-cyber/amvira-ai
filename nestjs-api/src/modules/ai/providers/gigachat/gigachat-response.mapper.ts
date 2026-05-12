import type { LlmInvocationResponse } from '../../contracts/llm.invocation';
import type { GigachatChatCompletionResponse } from './gigachat.types';
import { GigachatError } from './gigachat.errors';

export type GigachatParsedCompletion = {
  readonly llm: LlmInvocationResponse;
  readonly usageLog?: Readonly<{
    promptTokens?: number;
    completionTokens?: number;
    totalTokens?: number;
  }>;
};

/**
 * Parses GigaChat chat/completions JSON and maps to {@link LlmInvocationResponse}.
 * Wraps assistant plain text as JSON so {@link DefaultAiResponseValidator} stays unchanged.
 */
export function mapGigachatChatCompletionToLlmResponse(
  json: unknown,
): GigachatParsedCompletion {
  if (!json || typeof json !== 'object') {
    throw new GigachatError(
      'GigaChat response is not an object',
      'malformed_response',
      false,
      undefined,
    );
  }
  const body = json as GigachatChatCompletionResponse;
  if (body.error) {
    const code = body.error.code;
    const retryable =
      code === 429 || (typeof code === 'number' && code >= 500) || code === undefined;
    throw new GigachatError(
      body.error.message ?? 'gigachat_provider_error',
      'provider_error',
      retryable,
      undefined,
      typeof code === 'number' ? code : undefined,
    );
  }
  const choice = body.choices?.[0];
  const content = choice?.message?.content ?? '';
  const finishReason = choice?.finish_reason ?? 'stop';
  const trimmed = content.trim();
  const refusedByFilter = finishReason === 'content_filter';
  const refusedEmpty = trimmed.length === 0;
  const refused = refusedByFilter || refusedEmpty;
  const refusalReason = refusedByFilter
    ? 'content_filter'
    : refusedEmpty
      ? 'empty_model_output'
      : undefined;
  const rawText = JSON.stringify({
    replyText: refused ? '' : trimmed,
    refused,
    refusalReason,
  });
  const usage = body.usage;
  return {
    llm: {
      rawText,
      finishReason,
    },
    usageLog: usage
      ? {
          promptTokens: usage.prompt_tokens,
          completionTokens: usage.completion_tokens,
          totalTokens: usage.total_tokens,
        }
      : undefined,
  };
}
