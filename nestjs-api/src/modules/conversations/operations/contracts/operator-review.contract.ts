/**
 * Operator review surface — no RBAC here; caller supplies operator identity when available.
 */
export type OperatorReviewSnapshotV1 = {
  readonly reviewVersion: 'operator_review@v1';
  readonly dialogId: string;
  readonly reviewedAt: string;
  readonly operatorLabel?: string;
  readonly summary: string;
  readonly requiresFollowUp: boolean;
};
