import type { PromptBlock, PromptBlockContext } from './prompt-block.contract';
import { orderedFactsJson } from '../../retrieval/prioritization/retrieval-fact-prioritizer';
import {
  ALLOWED_BUSINESS_FACT_CATEGORIES,
  FORBIDDEN_BUSINESS_CLAIMS,
  STALE_DATA_BEHAVIOR,
  UNAVAILABLE_DATA_BEHAVIOR,
} from '../../retrieval/policies/retrieval-access.policy';

function bullet(title: string, items: readonly string[]): string {
  return `${title}\n${items.map((x) => `- ${x}`).join('\n')}`;
}

export const GROUNDING_BOUNDARIES_BLOCK: PromptBlock = {
  id: 'grounding.boundaries',
  lane: 'system',
  render: ({ context }: PromptBlockContext) => {
    const keys = context.allowedFactKeys.length
      ? context.allowedFactKeys.map((k) => `- ${k}`).join('\n')
      : '- (none declared — treat as no factual anchors beyond user text)';
    const sources = context.allowedFactSources.length
      ? context.allowedFactSources.map((s) => `- ${s}`).join('\n')
      : '- dialog.snapshot';
    return [
      'GROUNDING FACTS — you may only treat the following snapshot keys as factual anchors when echoed or paraphrased:',
      keys,
      '',
      'Allowed fact source kinds (vocabulary only — no live fetch):',
      sources,
      '',
      'Do not invent salon-specific facts (staff on duty, promotions, stock) unless present in the user message or listed keys.',
    ].join('\n');
  },
};

export const CONTEXT_SNAPSHOT_BLOCK: PromptBlock = {
  id: 'grounding.snapshot',
  lane: 'system',
  render: ({ context }: PromptBlockContext) =>
    [
      'READ-ONLY DIALOG SNAPSHOT (for tone and continuity only — not approval to act):',
      `- dialogId: ${context.dialogId}`,
      `- channel: ${context.channel}`,
      `- currentStage: ${context.currentStage}`,
      `- dialogStatus: ${context.dialogStatus}`,
      context.scenarioCode ? `- scenarioCode: ${context.scenarioCode}` : '- scenarioCode: (none)',
    ].join('\n'),
};

export const BUSINESS_CONTEXT_SNAPSHOT_BLOCK: PromptBlock = {
  id: 'grounding.business_retrieval',
  lane: 'system',
  render: ({ context }: PromptBlockContext) => {
    if (!context.businessSnapshot) {
      return '';
    }
    const { facts, trace } = context.businessSnapshot;
    const orderedKeys =
      context.orderedBusinessFactKeys ?? Object.keys(facts);
    const trimmed = orderedFactsJson(facts, orderedKeys, 4000);
    const traceJson = JSON.stringify(trace.providers);
    return [
      'RETRIEVAL GROUNDING SNAPSHOT (read-only; not memory; may be stale; keys ordered by business priority):',
      trimmed,
      '',
      'Retrieval trace (deterministic provider order):',
      traceJson,
      '',
      STALE_DATA_BEHAVIOR,
      UNAVAILABLE_DATA_BEHAVIOR,
      '',
      bullet('Allowed business fact categories (when present in JSON above)', [
        ...ALLOWED_BUSINESS_FACT_CATEGORIES,
      ]),
      '',
      bullet('Forbidden business claims', [...FORBIDDEN_BUSINESS_CLAIMS]),
    ].join('\n');
  },
};
