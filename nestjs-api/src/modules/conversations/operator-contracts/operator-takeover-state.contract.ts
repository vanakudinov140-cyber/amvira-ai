/**
 * Transient takeover flag returned to callers (session / gateway); not persisted here.
 */
export type OperatorTakeoverStateV1 = {
  readonly stateVersion: 'operator_takeover_state@v1';
  readonly active: boolean;
  readonly source: 'command_execution';
};
