/**
 * Recoverable: caller may retry later (e.g. transient provider) without mutating FSM.
 * Non-recoverable: invariant violated or duplicate suppressed — retry without change is pointless.
 */
export type OrchestrationFailureRecoverability =
  | 'recoverable'
  | 'non_recoverable';

export class ConversationAiTimeoutError extends Error {
  constructor(
    message: string,
    public readonly correlationId?: string,
  ) {
    super(message);
    this.name = 'ConversationAiTimeoutError';
  }
}

export function classifyOrchestrationFailure(
  error: unknown,
): OrchestrationFailureRecoverability {
  if (error instanceof ConversationAiTimeoutError) {
    return 'recoverable';
  }
  if (error instanceof Error) {
    const m = error.message.toLowerCase();
    if (m.includes('timeout') || m.includes('timed out')) {
      return 'recoverable';
    }
  }
  return 'non_recoverable';
}
