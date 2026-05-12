export type EscalationVisibilityV1 = {
  readonly version: 'escalation_visibility@v1';
  readonly escalationIntentPresent: boolean;
  readonly queueRoutingConfirmed: boolean;
  readonly source: 'last_operations_envelope' | 'unknown';
};
