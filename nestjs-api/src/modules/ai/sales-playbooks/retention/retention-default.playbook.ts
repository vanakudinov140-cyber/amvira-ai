import type { SalesPlaybookDefinition } from '../sales-playbook.contract';

export const RETENTION_DEFAULT_PLAYBOOK: SalesPlaybookDefinition = {
  id: 'retention.default',
  category: 'retention',
  title: 'Retention — nurture and upsell with consent',
  goals: [
    'Increase repeat visits with relevant, grounded suggestions.',
    'Protect trust: no invented offers.',
  ],
  allowedTactics: [
    'Suggest adjacent services only if aligned with stated preferences.',
    'One soft upsell per turn maximum.',
  ],
  forbiddenTactics: [
    'Hard selling unrelated bundles.',
    'Claiming discounts not in snapshot.',
  ],
  transitionConditions: [
    'If guest declines twice → pivot to service quality check-in.',
  ],
  examplePhrasing: [
    'Часто после этой услуги гости делают … — интересно обсудить или оставим как есть?',
    'Могу напомнить про следующий визит — какой ритм вам комфортнее: раз в месяц или реже?',
  ],
  escalationRules: [
    'Escalate on billing issues or complaints about prior visit.',
  ],
};
