import type { SalesToolIntent } from './tool-intent.contract';

export type ToolExecutionRecoverability = 'recoverable' | 'non_recoverable';

export type ToolExecutionItemResult = {
  readonly intentId: string;
  readonly toolId: string;
  readonly kind: 'success' | 'skipped' | 'failed';
  readonly detail?: string;
  readonly payload?: Readonly<Record<string, unknown>>;
  readonly recoverability?: ToolExecutionRecoverability;
};

export type ToolExecutionBatchResult = {
  readonly version: 'tool_execution_batch@v1';
  readonly items: readonly ToolExecutionItemResult[];
};

export type ToolProposalValidation = {
  readonly ok: boolean;
  readonly reason?: string;
};

/**
 * Deterministic proposal — AI never executes; orchestrator owns execution.
 */
export type SalesToolProposal = {
  readonly proposalId: string;
  readonly intent: SalesToolIntent;
  readonly validation: ToolProposalValidation;
};

export type ToolExecutionContext = {
  readonly dialogId: string;
  readonly clientId: string;
  readonly currentStage: string;
  readonly dialogStatus: string;
  readonly executeTools: boolean;
  readonly confirmedIntentIds: ReadonlySet<string>;
  /** Set by orchestrator for the active proposal row. */
  readonly activeIntentId: string;
  readonly bookingPayload?: Readonly<{
    service: string;
    datetime: string;
    notes?: string;
    /** Optional YCLIENTS entity ids when channel/UI resolved them. */
    yclientsServiceId?: number;
    yclientsStaffId?: number;
  }>;
};
