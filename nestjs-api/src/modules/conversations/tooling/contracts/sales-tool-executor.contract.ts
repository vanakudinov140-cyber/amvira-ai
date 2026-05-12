import type { SalesToolId } from './tool-intent.contract';
import type {
  ToolExecutionContext,
  ToolExecutionItemResult,
} from './tool-execution.contract';

export interface SalesToolExecutor {
  readonly toolId: SalesToolId;
  execute(
    ctx: ToolExecutionContext,
    params: Readonly<Record<string, unknown>>,
  ): Promise<ToolExecutionItemResult>;
}
