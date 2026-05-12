import type { SalesPlaybookDefinition } from '../sales-playbook.contract';

export const BOOKING_CONVERSION_DEFAULT_PLAYBOOK: SalesPlaybookDefinition = {
  id: 'booking_conversion.default',
  category: 'booking_conversion',
  title: 'Booking conversion — gentle momentum',
  goals: [
    'Convert interest into a concrete next step using only grounded availability.',
    'Keep momentum without sounding robotic.',
  ],
  allowedTactics: [
    'Offer one clear CTA (pick slot / confirm service / share phone).',
    'Mirror guest language; keep replies compact.',
  ],
  forbiddenTactics: [
    'Inventing slots, staff, or policies.',
    'Double-barreled questions.',
    'Giant paragraphs.',
  ],
  transitionConditions: [
    'If booking readiness is high and facts allow → propose time selection grounded in snapshot.',
    'If readiness is medium → confirm service + constraints first.',
  ],
  examplePhrasing: [
    'Могу зафиксировать время. Удобнее ближайшие дни днём или вечером?',
    'Если выберете услугу из списка в контексте — подберу ближайший свободный слот из доступных.',
  ],
  escalationRules: [
    'Escalate if guest needs exceptions, complaints, or payment disputes.',
  ],
};
