export const ESCALATION_RESOLUTION_CODES = [
  'resolved_by_operator',
  'resolved_false_alarm',
  'routed_elsewhere',
  'other',
] as const;

export type EscalationResolutionCodeV1 =
  (typeof ESCALATION_RESOLUTION_CODES)[number];

export type EscalationResolutionPayloadV1 = {
  readonly resolutionCode: EscalationResolutionCodeV1;
  readonly note?: string;
};
