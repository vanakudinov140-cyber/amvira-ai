import type { ApplicationEvent } from '../../../shared/events/application-event';
import { APPLICATION_EVENT_TYPE } from '../../../shared/events/application-event-type';

export type BookingStatusChangedPayload = {
  bookingId: string;
  clientId: string;
  previousStatus: string;
  newStatus: string;
};

export function bookingStatusChangedEvent(
  payload: BookingStatusChangedPayload,
): ApplicationEvent<BookingStatusChangedPayload> {
  return {
    type: APPLICATION_EVENT_TYPE.BOOKING_STATUS_CHANGED,
    occurredAt: new Date(),
    payload: { ...payload },
  };
}
