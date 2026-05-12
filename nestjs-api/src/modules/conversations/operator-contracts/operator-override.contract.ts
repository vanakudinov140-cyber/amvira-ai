/** Operator acknowledges manual override boundary without invoking AI. */
export type OperatorAssistantOverrideV1 = {
  readonly overrideVersion: 'operator_assistant_override@v1';
  readonly acknowledged: boolean;
  readonly note?: string;
};
