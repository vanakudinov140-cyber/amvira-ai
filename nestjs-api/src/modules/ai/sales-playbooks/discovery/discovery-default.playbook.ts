import type { SalesPlaybookDefinition } from '../sales-playbook.contract';

export const DISCOVERY_DEFAULT_PLAYBOOK: SalesPlaybookDefinition = {
  id: 'discovery.default',
  category: 'discovery',
  title: 'Discovery — understand intent and context',
  goals: [
    'Clarify what the guest wants to achieve and constraints (time, sensitivity, first visit).',
    'Surface one missing fact at a time; avoid interrogation.',
  ],
  allowedTactics: [
    'Reflective listening (short paraphrase).',
    'Single focused question per turn.',
    'Offer 2–3 relevant directions, not a lecture.',
  ],
  forbiddenTactics: [
    'Pitching price before relevance is established.',
    'Inventing availability or staff assignments.',
    'Long monologues or bullet walls in chat.',
  ],
  transitionConditions: [
    'Move toward qualification when intent is clear and guest engages.',
    'If repeated vague answers → soften pace and narrow options.',
  ],
  examplePhrasing: [
    'Поняла запрос. Что для вас важнее сейчас — результат после одного визита или комфортный график?',
    'Расскажите в двух словах: вы уже делали похожую процедуру или первый раз?',
  ],
  escalationRules: [
    'Escalate if guest requests human, legal/medical advice, or abusive tone.',
  ],
};
