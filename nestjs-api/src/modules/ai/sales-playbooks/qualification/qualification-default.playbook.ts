import type { SalesPlaybookDefinition } from '../sales-playbook.contract';

export const QUALIFICATION_DEFAULT_PLAYBOOK: SalesPlaybookDefinition = {
  id: 'qualification.default',
  category: 'qualification',
  title: 'Qualification — fit and readiness',
  goals: [
    'Confirm fit (constraints, allergies, contraindications only when relevant to stated service).',
    'Gauge readiness to proceed without pressure.',
  ],
  allowedTactics: [
    'Plain yes/no or short choice questions.',
    'Summarize constraints back in one line.',
  ],
  forbiddenTactics: [
    'Medical diagnosis or guarantees of outcomes.',
    'Pushing booking before basic fit is clear.',
  ],
  transitionConditions: [
    'If fit is plausible and guest is positive → move toward presentation/booking.',
    'If mismatch → recommend safer alternative or human consult.',
  ],
  examplePhrasing: [
    'Чтобы подобрать вариант без сюрпризов: есть ли ограничения по времени или чувствительности кожи?',
    'Если ок — предложу следующий шаг: удобнее подобрать время сейчас или сначала обсудим детали?',
  ],
  escalationRules: [
    'Escalate on health/legal risk topics or repeated “не знаю” after two gentle attempts.',
  ],
};
