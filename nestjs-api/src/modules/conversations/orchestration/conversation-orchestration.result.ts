import type { AssistantReplyCandidate } from '../contracts/assistant-reply-candidate';
import type { AssistantReplyQualityReportV1 } from '../../ai/quality/assistant-reply-quality.evaluator';
import type { AiSalesDecisionEnvelope } from '../../ai/sales-decisions/contracts/ai-sales-decision.contract';
import type { AsyncJobDispatchResult } from '../../../shared/async/async-job-result.contract';
import type {
  SalesToolProposal,
  ToolExecutionBatchResult,
} from '../tooling/contracts/tool-execution.contract';
import type { DeliveryReceipt } from '../../../shared/integrations/delivery-receipt.contract';
import type { OperationsEnvelopeV1 } from '../operations/contracts/operations-envelope.contract';

export type ConversationOrchestrationStatus =
  | 'completed'
  | 'completed_with_assistant_persist_warning'
  | 'completed_with_delivery_warning'
  | 'partial_ai_refused'
  | 'partial_ai_failed'
  | 'partial_ai_timeout'
  | 'blocked_dialog'
  | 'blocked_dialog_not_found'
  | 'failed_user_message_persist'
  | 'duplicate_turn_suppressed';

/**
 * Normalized delivery outcome (distinct from persisted assistant row).
 */
export type ConversationDeliveryOutcome =
  | { readonly kind: 'skipped' }
  | { readonly kind: 'sync_delivered'; readonly receipt: DeliveryReceipt }
  | { readonly kind: 'sync_failed'; readonly error: string }
  | {
      readonly kind: 'async_enqueued';
      readonly dispatch: AsyncJobDispatchResult;
    }
  | { readonly kind: 'async_enqueue_failed'; readonly error: string };

/**
 * persisted USER/ASSISTANT rows vs generated candidate vs channel delivery.
 */
export type ConversationOrchestrationResult = {
  readonly status: ConversationOrchestrationStatus;
  readonly dialogId: string;
  readonly correlationId?: string;
  readonly userMessageId?: string;
  /** Persisted assistant row (MessagesService), if any. */
  readonly assistantMessageId?: string;
  /** Model output snapshot (not necessarily persisted). */
  readonly candidate?: AssistantReplyCandidate;
  /** Raw receipt when sync path succeeded (legacy field). */
  readonly deliveryReceipt?: DeliveryReceipt;
  /** Unified delivery semantics. */
  readonly deliveryOutcome?: ConversationDeliveryOutcome;
  /** AI sales decision proposal — FSM must not auto-apply; human or policy gate consumes this. */
  readonly aiSalesDecision?: AiSalesDecisionEnvelope;
  /** Deterministic tool intents derived from sales decision — not executed unless {@link UserMessageOrchestrationRequest.executeTools}. */
  readonly toolProposals?: readonly SalesToolProposal[];
  readonly toolExecution?: ToolExecutionBatchResult;
  /** Human handoff / operator routing snapshot for this turn (contracts only; no persistence here). */
  readonly operationsEnvelope?: OperationsEnvelopeV1;
  readonly aiRefusal?: {
    readonly reason: string;
    readonly detail?: string;
  };
  /** Present when AI path used deterministic recovery copy instead of provider JSON. */
  readonly aiReplyMeta?: Readonly<{
    readonly usedFallback: boolean;
    readonly fallbackReason?: string;
    readonly priorFailureReason?: string;
    readonly priorFailureDetail?: string;
  }>;
  readonly assistantReplyQuality?: AssistantReplyQualityReportV1;
  readonly recoverability?: 'recoverable' | 'non_recoverable';
};
