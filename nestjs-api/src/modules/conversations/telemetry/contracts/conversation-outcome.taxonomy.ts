import type { ConversationOrchestrationStatus } from '../../orchestration/conversation-orchestration.result';

/**
 * Coarse analytics outcome — orthogonal to {@link ConversationOrchestrationStatus}.
 */
export const CONVERSATION_ANALYTICS_OUTCOMES = [
  'success_completed',
  'success_with_warnings',
  'blocked',
  'ai_partial_failure',
  'user_persist_failure',
  'duplicate_or_replay',
  'unknown',
] as const;

export type ConversationAnalyticsOutcome =
  (typeof CONVERSATION_ANALYTICS_OUTCOMES)[number];

export function mapOrchestrationStatusToAnalyticsOutcome(
  status: ConversationOrchestrationStatus,
): ConversationAnalyticsOutcome {
  switch (status) {
    case 'completed':
      return 'success_completed';
    case 'completed_with_assistant_persist_warning':
    case 'completed_with_delivery_warning':
      return 'success_with_warnings';
    case 'blocked_dialog':
    case 'blocked_dialog_not_found':
      return 'blocked';
    case 'partial_ai_refused':
    case 'partial_ai_failed':
    case 'partial_ai_timeout':
      return 'ai_partial_failure';
    case 'failed_user_message_persist':
      return 'user_persist_failure';
    case 'duplicate_turn_suppressed':
      return 'duplicate_or_replay';
    default:
      return 'unknown';
  }
}
