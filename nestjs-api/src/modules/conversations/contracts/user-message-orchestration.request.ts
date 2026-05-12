import type { OperatorOrchestrationContextV1 } from '../operations/contracts/operator-orchestration-context.contract';

/**
 * Inbound user turn — not yet persisted; orchestration owns persistence ordering.
 */
export type UserMessageOrchestrationRequest = {
  readonly dialogId: string;
  readonly userText: string;
  readonly correlationId?: string;
  /**
   * Client-supplied dedupe key for this turn (process-local cache only).
   * Same dialogId + key within TTL returns the prior orchestration snapshot.
   */
  readonly turnIdempotencyKey?: string;
  /** When true, persist assistant reply after successful AI path (decoupled from AI layer). */
  readonly persistAssistantMessage?: boolean;
  /** When true, invoke {@link ChannelAdapter.deliver} after candidate is available. */
  readonly dispatchToChannel?: boolean;
  /** When true with {@link dispatchToChannel}, enqueue via {@link AsyncJobDispatcher} instead of sync deliver. */
  readonly deferChannelDispatch?: boolean;
  /**
   * Channel-specific opaque metadata (e.g. Telegram chat id) passed to {@link ChannelAdapter.deliver}.
   */
  readonly channelMetadata?: Readonly<Record<string, unknown>>;
  /**
   * When true, run {@link ToolExecutionOrchestrator} for validated proposals.
   * Mutating tools still require per-intent confirmation ids.
   */
  readonly executeTools?: boolean;
  readonly toolExecutionContext?: Readonly<{
    readonly confirmedIntentIds: readonly string[];
    readonly bookingPayload?: Readonly<{
      service: string;
      datetime: string;
      notes?: string;
      yclientsServiceId?: number;
      yclientsStaffId?: number;
    }>;
  }>;
  /** Operator / control-plane signals — never inferred from model output inside the orchestrator. */
  readonly operatorContext?: OperatorOrchestrationContextV1;
  /** Optional opaque ids for log/metrics correlation (not persisted by orchestration). */
  readonly telemetryContext?: Readonly<{
    readonly traceId?: string;
    readonly parentSpanId?: string;
  }>;
};
