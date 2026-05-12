import type { AiAssembledContext } from '../context/ai-context.builder';
import type { AiRoutingAllowed } from '../policies/ai-policy.evaluator';

export type AiPromptBundle = {
  readonly systemSlot: string;
  readonly userSlot: string;
  /** Optional tracing for logs / future metrics — not sent to models beyond slots unless you choose to. */
  readonly trace?: AiPromptTrace;
};

export type AiPromptTrace = {
  readonly promptVersion: string;
  readonly versionHash: string;
  readonly stageKey: string;
  readonly scenarioKey: string;
  readonly toneKey: string;
  readonly blockIds: readonly string[];
};

export const AI_PROMPT_COMPOSER = Symbol('AI_PROMPT_COMPOSER');

/**
 * Composes prompt slots from context + routing — no prompt library / templates here.
 */
export interface AiPromptComposer {
  compose(
    context: AiAssembledContext,
    routing: AiRoutingAllowed,
  ): Promise<AiPromptBundle>;
}
