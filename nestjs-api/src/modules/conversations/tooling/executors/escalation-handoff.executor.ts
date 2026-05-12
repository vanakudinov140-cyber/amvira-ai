import { Injectable } from '@nestjs/common';
import type { SalesToolExecutor } from '../contracts/sales-tool-executor.contract';
import type { ToolExecutionContext, ToolExecutionItemResult } from '../contracts/tool-execution.contract';

@Injectable()
export class EscalationHandoffExecutor implements SalesToolExecutor {
  readonly toolId = 'sales.escalation_handoff' as const;

  async execute(
    ctx: ToolExecutionContext,
    params: Readonly<Record<string, unknown>>,
  ): Promise<ToolExecutionItemResult> {
    return {
      intentId: ctx.activeIntentId,
      toolId: this.toolId,
      kind: 'success',
      payload: {
        dialogId: ctx.dialogId,
        reason: params.reason,
        note: 'no_side_effects_record_only',
      },
    };
  }
}
