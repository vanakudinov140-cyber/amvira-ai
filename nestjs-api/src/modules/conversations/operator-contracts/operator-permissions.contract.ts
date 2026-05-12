/**
 * Fine-grained capability strings — authorization is enforced only when
 * {@link OperatorCommandEnvelopeV1.authorization} is present.
 */
export const OPERATOR_PERMISSIONS = [
  'dialog:read',
  'dialog:reply',
  'dialog:stage_transition',
  'takeover:signal',
  'escalation:resolve',
  'assistant:override_ack',
] as const;

export type OperatorPermissionV1 = (typeof OPERATOR_PERMISSIONS)[number];

export type OperatorAuthorizationContextV1 = {
  readonly contextVersion: 'operator_authorization@v1';
  readonly granted: readonly OperatorPermissionV1[];
};
