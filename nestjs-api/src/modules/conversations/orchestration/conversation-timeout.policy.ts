import { ConversationAiTimeoutError } from './conversation-orchestration.errors';

/** Wall-clock bound for AI suggest — isolates slow LLM from request thread semantics. */
export const CONVERSATION_AI_SUGGEST_TIMEOUT_MS = 15_000;

export async function withConversationTimeout<T>(
  ms: number,
  correlationId: string | undefined,
  run: () => Promise<T>,
): Promise<T> {
  let timeoutId: ReturnType<typeof setTimeout> | undefined;
  const timeoutPromise = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(() => {
      reject(
        new ConversationAiTimeoutError(
          `AI suggest exceeded ${ms}ms`,
          correlationId,
        ),
      );
    }, ms);
  });
  try {
    return await Promise.race([run(), timeoutPromise]);
  } finally {
    if (timeoutId !== undefined) {
      clearTimeout(timeoutId);
    }
  }
}
