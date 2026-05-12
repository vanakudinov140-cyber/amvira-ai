import type { AssistantReplyCandidate } from './assistant-reply-candidate';

/**
 * Future: block/allow assistant drafts before persistence/dispatch (no implementation here).
 */
export interface ConversationModerationPort {
  evaluateAssistantDraft(
    candidate: AssistantReplyCandidate,
  ): Promise<{ readonly allowed: boolean; readonly reason?: string }>;
}

/**
 * Future: route to human operator (no implementation here).
 */
export interface HumanEscalationPort {
  shouldEscalate(candidate: AssistantReplyCandidate): Promise<boolean>;
}
