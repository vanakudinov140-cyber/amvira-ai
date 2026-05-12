import { Injectable } from '@nestjs/common';
import type { PromptBlock } from '../blocks/prompt-block.contract';

const SCENARIO_FRAGMENTS: Readonly<Record<string, string>> = {
  default:
    'Scenario: default conversational sales — assist with phrasing only.',
  booking_followup:
    'Scenario: booking follow-up — emphasize clarity and next steps the user already mentioned; never confirm schedule details without grounding.',
  reactivation:
    'Scenario: reactivation — polite check-in; avoid implying you know outcomes of past visits unless stated by the user.',
};

function normalizeScenario(code?: string): string {
  if (!code?.trim()) {
    return 'default';
  }
  const c = code.trim().toLowerCase();
  if (c in SCENARIO_FRAGMENTS) {
    return c;
  }
  if (c.includes('book')) {
    return 'booking_followup';
  }
  if (c.includes('react')) {
    return 'reactivation';
  }
  return 'default';
}

export function scenarioStrategyKey(code?: string): string {
  return normalizeScenario(code);
}

export function scenarioPromptBlocks(scenarioCode?: string): readonly PromptBlock[] {
  const key = normalizeScenario(scenarioCode);
  const text = SCENARIO_FRAGMENTS[key] ?? SCENARIO_FRAGMENTS.default;
  return [
    {
      id: `scenario.${key}`,
      lane: 'system',
      render: () => text,
    },
  ];
}

@Injectable()
export class ScenarioPromptRegistry {
  strategyKey(code?: string): string {
    return scenarioStrategyKey(code);
  }

  blocksFor(scenarioCode?: string): readonly PromptBlock[] {
    return scenarioPromptBlocks(scenarioCode);
  }
}
