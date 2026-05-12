import { Injectable } from '@nestjs/common';
import type {
  SalesToolProposal,
  ToolExecutionBatchResult,
  ToolExecutionContext,
  ToolExecutionItemResult,
} from '../contracts/tool-execution.contract';
import { isIntentConfirmed } from '../policies/tool-confirmation.policy';
import {
  isRecoverableToolError,
  MAX_TOOL_ATTEMPTS,
} from '../policies/tool-safe-execution.policy';
import { SalesToolRegistry } from '../registry/sales-tool.registry';

@Injectable()
export class ToolExecutionOrchestrator {
  constructor(private readonly registry: SalesToolRegistry) {}

  async run(
    proposals: readonly SalesToolProposal[],
    baseCtx: Omit<ToolExecutionContext, 'activeIntentId'>,
  ): Promise<ToolExecutionBatchResult> {
    const items: ToolExecutionItemResult[] = [];
    for (const p of proposals) {
      if (!p.validation.ok) {
        items.push({
          intentId: p.intent.intentId,
          toolId: p.intent.toolId,
          kind: 'skipped',
          detail: p.validation.reason ?? 'invalid_proposal',
        });
        continue;
      }
      const exec = this.registry.get(p.intent.toolId);
      if (!exec) {
        items.push({
          intentId: p.intent.intentId,
          toolId: p.intent.toolId,
          kind: 'failed',
          detail: 'unknown_tool',
          recoverability: 'non_recoverable',
        });
        continue;
      }
      if (
        p.intent.requiresConfirmation &&
        !isIntentConfirmed(p.intent.intentId, baseCtx.confirmedIntentIds)
      ) {
        items.push({
          intentId: p.intent.intentId,
          toolId: p.intent.toolId,
          kind: 'skipped',
          detail: 'confirmation_required',
        });
        continue;
      }

      const ctx: ToolExecutionContext = {
        ...baseCtx,
        activeIntentId: p.intent.intentId,
      };

      let lastErr: unknown;
      let result: ToolExecutionItemResult | undefined;
      for (let attempt = 1; attempt <= MAX_TOOL_ATTEMPTS; attempt++) {
        try {
          result = await exec.execute(ctx, p.intent.params);
          break;
        } catch (e) {
          lastErr = e;
          if (!isRecoverableToolError(e) || attempt >= MAX_TOOL_ATTEMPTS) {
            result = {
              intentId: p.intent.intentId,
              toolId: p.intent.toolId,
              kind: 'failed',
              detail: e instanceof Error ? e.message : String(e),
              recoverability: isRecoverableToolError(e)
                ? 'recoverable'
                : 'non_recoverable',
            };
            break;
          }
        }
      }
      items.push(
        result ?? {
          intentId: p.intent.intentId,
          toolId: p.intent.toolId,
          kind: 'failed',
          detail: lastErr instanceof Error ? lastErr.message : String(lastErr),
          recoverability: 'non_recoverable',
        },
      );
    }
    return { version: 'tool_execution_batch@v1', items };
  }
}
