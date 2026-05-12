import type { AuditTrailEntryV1 } from './audit-trail.contract';
import type { HumanHandoffDecisionV1 } from './human-handoff-decision.contract';
import type { TakeoverStateV1 } from './takeover.contract';

export type InterventionClassification =
  | 'no_intervention'
  | 'escalation_suggested'
  | 'escalation_routed'
  | 'takeover_suggested'
  | 'takeover_active'
  | 'resume_pending';

export type InterventionResultV1 = {
  readonly resultVersion: 'intervention_result@v1';
  readonly dialogId: string;
  readonly classification: InterventionClassification;
  readonly handoff?: HumanHandoffDecisionV1;
  readonly takeover?: TakeoverStateV1;
  readonly audit: readonly AuditTrailEntryV1[];
};
