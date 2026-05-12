import { Injectable, Logger } from '@nestjs/common';
import type { ApplicationEvent } from '../../../shared/events/application-event';
import type { ApplicationEventHandler } from '../../../shared/events/application-event.handler';
import { APPLICATION_EVENT_TYPE } from '../../../shared/events/application-event-type';
import type { BookingCreatedPayload } from '../events/booking-created.event';

@Injectable()
export class BookingCreatedHandler implements ApplicationEventHandler {
  readonly eventType = APPLICATION_EVENT_TYPE.BOOKING_CREATED;
  private readonly logger = new Logger(BookingCreatedHandler.name);

  handle(event: Readonly<ApplicationEvent<Record<string, unknown>>>): void {
    const p = event.payload as BookingCreatedPayload;
    this.logger.debug(
      `booking.created bookingId=${p.bookingId} clientId=${p.clientId} status=${p.status}`,
    );
  }
}
