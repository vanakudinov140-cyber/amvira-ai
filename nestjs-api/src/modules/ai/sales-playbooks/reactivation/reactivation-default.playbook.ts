import type { SalesPlaybookDefinition } from '../sales-playbook.contract';

export const REACTIVATION_DEFAULT_PLAYBOOK: SalesPlaybookDefinition = {
  id: 'reactivation.default',
  category: 'reactivation',
  title: 'Reactivation — respectful win-back',
  goals: [
    'Re-open dialogue with low pressure.',
    'Offer a relevant reason to return based on snapshot signals only.',
  ],
  allowedTactics: [
    'Short check-in + single question.',
    'Reference prior context only if present in retrieval/history snapshot.',
  ],
  forbiddenTactics: [
    'Guilt-tripping or fabricated past visits.',
    'Bulk spam tone.',
  ],
  transitionConditions: [
    'If positive micro-signal → move to discovery.',
    'If silence pattern → one polite close, stop pushing.',
  ],
  examplePhrasing: [
    'Вы давно не были у нас — хотите подобрать удобное время на ближайшие дни?',
    'Если сейчас не актуально — напишите “позже”, и я не буду дублировать.',
  ],
  escalationRules: [
    'Escalate if guest signals STOP / unsubscribe intent.',
  ],
};
