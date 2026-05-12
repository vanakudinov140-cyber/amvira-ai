/**
 * Channel/integration delivery acknowledgement — separate from job ack and LLM success.
 */
export type DeliveryReceipt = {
  readonly idempotencyKey: string;
  readonly deliveredAt: Date;
  readonly channelKey?: string;
  readonly status: 'ack' | 'failed';
  readonly detail?: string;
};
