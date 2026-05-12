/**
 * Async job names for deferred YCLIENTS sync — enqueue only when worker supports them.
 * {@link AsyncJobsProcessor} must handle new types before production enqueue.
 */
export const YCLIENTS_BOOKING_ASYNC_JOB_TYPES = {
  BOOKING_SYNC: 'booking.yclients.sync',
  BOOKING_RESYNC: 'booking.yclients.resync',
  BOOKING_CANCEL_SYNC: 'booking.yclients.cancel.sync',
} as const;

export type BookingYclientsSyncJobPayloadV1 = Readonly<{
  readonly bookingId: string;
  readonly correlationId?: string;
}>;

export type BookingYclientsResyncJobPayloadV1 =
  BookingYclientsSyncJobPayloadV1;

export type BookingYclientsCancelSyncJobPayloadV1 = Readonly<{
  readonly bookingId: string;
  readonly yclientsRecordId: number;
  readonly correlationId?: string;
}>;
