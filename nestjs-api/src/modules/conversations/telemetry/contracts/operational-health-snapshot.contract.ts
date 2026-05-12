/**
 * Turn-local health flags — deterministic booleans for dashboards / SLO helpers.
 */
export type OperationalHealthSnapshotV1 = {
  readonly healthVersion: 'operational_health@v1';
  readonly turnCompleted: boolean;
  readonly turnCompletedWithWarnings: boolean;
  readonly aiCandidateProduced: boolean;
  readonly toolsExecutedCleanly: boolean;
  readonly deliveryAttempted: boolean;
  readonly deliverySucceeded: boolean;
};
