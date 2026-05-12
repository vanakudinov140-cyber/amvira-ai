import type { ApplicationEvent } from '../../../shared/events/application-event';
import { APPLICATION_EVENT_TYPE } from '../../../shared/events/application-event-type';

export type BookingCreatedPayload = {
  bookingId: string;
  clientId: string;
  status: string;
  datetimeIso: string;
};

export type BookingCreatedSource = {
  id: string;
  clientId: string;
  status: string;
  datetime: Date;
};

export function bookingCreatedEvent(
  source: BookingCreatedSource,
): ApplicationEvent<BookingCreatedPayload> {
  return {
    type: APPLICATION_EVENT_TYPE.BOOKING_CREATED,
    occurredAt: new Date(),
    payload: {
      bookingId: source.id,
      clientId: source.clientId,
      status: source.status,
      datetimeIso: source.datetime.toISOString(),
    },
  };
}
