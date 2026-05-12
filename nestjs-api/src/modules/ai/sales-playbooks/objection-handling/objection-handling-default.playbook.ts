import type { SalesPlaybookDefinition } from '../sales-playbook.contract';

export const OBJECTION_HANDLING_DEFAULT_PLAYBOOK: SalesPlaybookDefinition = {
  id: 'objection_handling.default',
  category: 'objection_handling',
  title: 'Objection handling — de-escalate and reframe',
  goals: [
    'Acknowledge the concern without arguing.',
    'Separate price/trust/timing issues; respond with one concrete next step.',
  ],
  allowedTactics: [
    'Label + validate (“Понимаю, что вопрос цены важен…”).',
    'Offer a smaller commitment (clarify scope, compare apples-to-apples).',
  ],
  forbiddenTactics: [
    'Discount promises not grounded in business snapshot.',
    'Shaming, urgency tricks, fake scarcity.',
  ],
  transitionConditions: [
    'If severity drops after one empathetic loop → return to discovery/qualification.',
    'If severity stays high → suggest operator handoff.',
  ],
  examplePhrasing: [
    'Согласна, что без прозрачности решать сложно. Могу коротко объяснить, из чего складывается ценность — ок?',
    'Если сроки не сходятся: какой ближайший интервал вам реалистичен — неделя или месяц?',
  ],
  escalationRules: [
    'Escalate if two cycles fail to reduce intensity or guest asks for manager.',
  ],
};
