import { Injectable } from '@nestjs/common';
import type { FollowUpScheduleContractV1 } from '../contracts/follow-up-schedule.contract';
import type { SalesToolExecutor } from '../contracts/sales-tool-executor.contract';
import type { ToolExecutionContext, ToolExecutionItemResult } from '../contracts/tool-execution.contract';

@Injectable()
export class FollowUpContractExecutor implements SalesToolExecutor {
  readonly toolId = 'follow_up.schedule_contract' as const;

  async execute(
    ctx: ToolExecutionContext,
    params: Readonly<Record<string, unknown>>,
  ): Promise<ToolExecutionItemResult> {
    const channel =
      typeof params.channel === 'string' ? params.channel : 'unspecified';
    const contract: FollowUpScheduleContractV1 = {
      contractVersion: 'follow_up.schedule@v1',
      dialogId: ctx.dialogId,
      suggestedChannel: channel,
      suggestedOffsetHours: [24, 72, 168],
      rationale: 'deterministic_follow_up_windows',
    };
    return {
      intentId: ctx.activeIntentId,
      toolId: this.toolId,
      kind: 'success',
      payload: { ...contract },
    };
  }
}
