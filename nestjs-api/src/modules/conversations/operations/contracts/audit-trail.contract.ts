export type AuditTrailEntryV1 = {
  readonly entryVersion: 'audit_trail@v1';
  readonly at: string;
  readonly actor: 'ai_suggestion' | 'ai_sales_decision' | 'tool_execution' | 'operator' | 'system';
  readonly event: string;
  readonly detail?: Readonly<Record<string, unknown>>;
};
