export type OperatorNoteV1 = {
  readonly noteVersion: 'operator_note@v1';
  readonly dialogId: string;
  readonly recordedAt: string;
  readonly body: string;
  readonly visibility: 'internal' | 'client_safe_summary';
};
