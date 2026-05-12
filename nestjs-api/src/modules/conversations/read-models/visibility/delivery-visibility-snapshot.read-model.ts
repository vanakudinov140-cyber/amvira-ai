export type DeliveryVisibilitySnapshotV1 = {
  readonly version: 'delivery_visibility@v1';
  readonly channel: string;
  /** Channel exists; last-mile delivery is not persisted on Dialog — unknown until channel receipts are linked. */
  readonly lastMileStatus: 'unknown';
  readonly source: 'dialog_channel_only';
};
