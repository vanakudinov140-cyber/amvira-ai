import type { AiAssembledContext } from '../../context/ai-context.builder';
import type { AiRoutingAllowed } from '../../policies/ai-policy.evaluator';

/**
 * Immutable unit of prompt text. Composed in a fixed pipeline — not a DSL.
 */
export type PromptBlockContext = {
  readonly context: AiAssembledContext;
  readonly routing: AiRoutingAllowed;
};

export type PromptBlock = {
  readonly id: string;
  /** Declarative lane for tracing / future split (e.g. tool-only). */
  readonly lane: 'system';
  readonly render: (ctx: PromptBlockContext) => string;
};
