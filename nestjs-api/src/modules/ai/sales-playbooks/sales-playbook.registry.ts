import { BOOKING_CONVERSION_DEFAULT_PLAYBOOK } from './booking-conversion/booking-conversion-default.playbook';
import { DISCOVERY_DEFAULT_PLAYBOOK } from './discovery/discovery-default.playbook';
import { OBJECTION_HANDLING_DEFAULT_PLAYBOOK } from './objection-handling/objection-handling-default.playbook';
import { QUALIFICATION_DEFAULT_PLAYBOOK } from './qualification/qualification-default.playbook';
import { REACTIVATION_DEFAULT_PLAYBOOK } from './reactivation/reactivation-default.playbook';
import { RETENTION_DEFAULT_PLAYBOOK } from './retention/retention-default.playbook';
import type { SalesPlaybookDefinition } from './sales-playbook.contract';

export const ALL_SALES_PLAYBOOKS: readonly SalesPlaybookDefinition[] = [
  DISCOVERY_DEFAULT_PLAYBOOK,
  QUALIFICATION_DEFAULT_PLAYBOOK,
  OBJECTION_HANDLING_DEFAULT_PLAYBOOK,
  BOOKING_CONVERSION_DEFAULT_PLAYBOOK,
  REACTIVATION_DEFAULT_PLAYBOOK,
  RETENTION_DEFAULT_PLAYBOOK,
];

export const SALES_PLAYBOOK_BY_ID: Readonly<Record<string, SalesPlaybookDefinition>> =
  Object.fromEntries(ALL_SALES_PLAYBOOKS.map((p) => [p.id, p]));
