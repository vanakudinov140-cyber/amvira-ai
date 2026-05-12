/**
 * Declarative sales playbooks — no LLM calls; consumed by prompt composer + selector.
 */
export type SalesPlaybookId = string;

export type SalesPlaybookCategory =
  | 'discovery'
  | 'qualification'
  | 'objection_handling'
  | 'booking_conversion'
  | 'reactivation'
  | 'retention';

export type SalesPlaybookDefinition = Readonly<{
  readonly id: SalesPlaybookId;
  readonly category: SalesPlaybookCategory;
  readonly title: string;
  readonly goals: readonly string[];
  readonly allowedTactics: readonly string[];
  readonly forbiddenTactics: readonly string[];
  readonly transitionConditions: readonly string[];
  readonly examplePhrasing: readonly string[];
  readonly escalationRules: readonly string[];
}>;

export type SalesPlaybookSnapshotV1 = Readonly<{
  readonly snapshotVersion: 'sales_playbook@v1';
  readonly primary: SalesPlaybookDefinition;
  readonly supporting: readonly SalesPlaybookDefinition[];
  readonly selectionRationale: readonly string[];
}>;
