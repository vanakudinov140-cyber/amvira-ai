import type { PromptBlock } from './prompt-block.contract';
import {
  ALLOWED_ASSISTANT_CLAIMS,
  ESCALATION_PHRASES,
  FORBIDDEN_ASSISTANT_CLAIMS,
  FORBIDDEN_MANIPULATIONS,
} from '../policies/assistant-constraints.constants';
import {
  ALLOWED_PERSUASION_TECHNIQUES,
  FORBIDDEN_PERSUASION_TECHNIQUES,
} from '../policies/persuasion-boundaries.constants';
import {
  REFUSAL_STRATEGY_LINES,
  UNCERTAINTY_BEHAVIOR_LINES,
} from '../policies/refusal-strategy.constants';

function bulletList(title: string, items: readonly string[]): string {
  return `${title}\n${items.map((x) => `- ${x}`).join('\n')}`;
}

export const CORE_IDENTITY_BLOCK: PromptBlock = {
  id: 'core.identity',
  lane: 'system',
  render: () =>
    [
      'You assist staff with customer-facing wording for a beauty salon conversational flow.',
      'You are not authoritative: business rules, pricing, and scheduling are owned by the host application (FSM), not by you.',
      'Output must be a single JSON object as instructed elsewhere (replyText, refused, optional refusalReason).',
    ].join('\n'),
};

export const CONSTRAINTS_BLOCK: PromptBlock = {
  id: 'core.constraints',
  lane: 'system',
  render: () =>
    [
      bulletList('Allowed assistant claims', ALLOWED_ASSISTANT_CLAIMS),
      '',
      bulletList('Forbidden claims', FORBIDDEN_ASSISTANT_CLAIMS),
      '',
      bulletList('Forbidden manipulations', FORBIDDEN_MANIPULATIONS),
      '',
      bulletList('Escalation / handoff phrasing', ESCALATION_PHRASES),
    ].join('\n'),
};

export const PERSUASION_POLICY_BLOCK: PromptBlock = {
  id: 'core.persuasion_policy',
  lane: 'system',
  render: () =>
    [
      bulletList('Allowed persuasion techniques', ALLOWED_PERSUASION_TECHNIQUES),
      '',
      bulletList('Forbidden persuasion techniques', FORBIDDEN_PERSUASION_TECHNIQUES),
    ].join('\n'),
};

export const REFUSAL_UNCERTAINTY_BLOCK: PromptBlock = {
  id: 'core.refusal_uncertainty',
  lane: 'system',
  render: () =>
    [
      bulletList('Refusal strategy', REFUSAL_STRATEGY_LINES),
      '',
      bulletList('Uncertainty behavior', UNCERTAINTY_BEHAVIOR_LINES),
    ].join('\n'),
};

export const CORE_PIPELINE_PREFIX: readonly PromptBlock[] = [
  CORE_IDENTITY_BLOCK,
  CONSTRAINTS_BLOCK,
  PERSUASION_POLICY_BLOCK,
  REFUSAL_UNCERTAINTY_BLOCK,
];
