export type HandoffTakeoverVisibilityV1 = {
  readonly version: 'handoff_takeover_visibility@v1';
  readonly takeoverActive: boolean;
  readonly takeoverSource: 'workspace_signal' | 'unknown';
  readonly handoffQueueRoutingActive: boolean;
  readonly handoffSource: 'last_operations_envelope' | 'unknown';
};
