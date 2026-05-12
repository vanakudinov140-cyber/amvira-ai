/**
 * Immutable audit line — append-only semantics at the model level (no mutation APIs).
 */
export type OperatorAuditLineV1 = {
  readonly lineVersion: 'operator_audit_line@v1';
  readonly tag: string;
  readonly detail: string;
};

export type OperatorAuditSnapshotV1 = {
  readonly auditVersion: 'operator_audit_snapshot@v1';
  readonly recordedAt: string;
  readonly dialogId: string;
  readonly correlationId?: string;
  readonly commandKind: string;
  readonly interventionKind: string;
  readonly outcomeStatus: string;
  readonly lines: readonly OperatorAuditLineV1[];
};
