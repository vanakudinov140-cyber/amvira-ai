export type ToolExecutionVisibilitySnapshotV1 = {
  readonly version: 'tool_execution_visibility@v1';
  readonly source: 'message_corpus';
  /** Count of persisted messages with role TOOL (when used as transcript storage). */
  readonly toolMessageCount: number;
};
