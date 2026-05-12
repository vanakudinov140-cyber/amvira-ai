/**
 * Foundation for unread / attention queues — no server-side read cursors yet.
 */
export type OperatorInboxUnreadSignalsV1 = {
  readonly version: 'operator_inbox_unread@v1';
  readonly lastMessageRole?: string;
  /** True when last persisted message is USER (operator may need to respond or review AI). */
  readonly suggestedPendingReview: boolean;
};
