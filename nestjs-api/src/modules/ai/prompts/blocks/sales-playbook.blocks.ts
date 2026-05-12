import type { PromptBlock, PromptBlockContext } from './prompt-block.contract';

function bullets(lines: readonly string[]): string {
  return lines.map((l) => `- ${l}`).join('\n');
}

export const SALES_PLAYBOOK_BLOCK: PromptBlock = {
  id: 'sales.playbook_snapshot',
  lane: 'system',
  render: ({ context }: PromptBlockContext) => {
    const pb = context.salesPlaybookSnapshot;
    if (!pb) {
      return '';
    }
    const sup = pb.supporting.map((s) => s.title).join('; ');
    return [
      'ACTIVE SALES PLAYBOOK (read-only — tactics are suggestions, not commands):',
      `Primary: ${pb.primary.title} [${pb.primary.id}]`,
      `Goals:\n${bullets(pb.primary.goals)}`,
      `Allowed tactics:\n${bullets(pb.primary.allowedTactics)}`,
      `Forbidden tactics:\n${bullets(pb.primary.forbiddenTactics)}`,
      `Transition conditions:\n${bullets(pb.primary.transitionConditions)}`,
      `Example phrasing (style only, do not copy verbatim if awkward):\n${bullets(pb.primary.examplePhrasing)}`,
      `Escalation rules:\n${bullets(pb.primary.escalationRules)}`,
      sup ? `Supporting playbooks: ${sup}` : '',
      `Selection rationale: ${pb.selectionRationale.join(' | ')}`,
    ]
      .filter(Boolean)
      .join('\n\n');
  },
};

export const CONVERSATION_MEMORY_BLOCK: PromptBlock = {
  id: 'sales.conversation_memory',
  lane: 'system',
  render: ({ context }: PromptBlockContext) => {
    const m = context.conversationMemory;
    if (!m) {
      return '';
    }
    return [
      'DETERMINISTIC CONVERSATION MEMORY (derived from retrieval/history snapshot — not live DB):',
      JSON.stringify(m),
    ].join('\n');
  },
};

export const SALES_BEHAVIOR_CONSTRAINTS_BLOCK: PromptBlock = {
  id: 'sales.behavior_constraints',
  lane: 'system',
  render: () =>
    [
      'Conversational sales behavior (non-negotiable):',
      '- Sound human and calm; avoid robotic filler (“как ИИ…”, over-apologies).',
      '- Do not repeat the same reassurance pattern twice in one reply.',
      '- Avoid giant paragraphs: prefer 2–4 short lines in chat.',
      '- Ask at most ONE logical question per turn.',
      '- Do not invent urgency, scarcity, or fake “last slot” claims.',
      '- Never hallucinate availability, staff, or prices: only use grounded snapshot keys.',
      '- If unsure, say what you can do next instead of guessing.',
    ].join('\n'),
};
