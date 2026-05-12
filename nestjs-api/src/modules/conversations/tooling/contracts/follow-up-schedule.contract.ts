/**
 * Immutable follow-up scheduling contract — no persistence here; consumer schedules elsewhere.
 */
export type FollowUpScheduleContractV1 = {
  readonly contractVersion: 'follow_up.schedule@v1';
  readonly dialogId: string;
  readonly suggestedChannel: string;
  readonly suggestedOffsetHours: readonly number[];
  readonly rationale: string;
};
