import { Injectable, Logger } from '@nestjs/common';
import type { ApplicationEvent } from '../../../shared/events/application-event';
import type { ApplicationEventHandler } from '../../../shared/events/application-event.handler';
import { APPLICATION_EVENT_TYPE } from '../../../shared/events/application-event-type';
import type { BookingStatusChangedPayload } from '../events/booking-status-changed.event';

@Injectable()
export class BookingStatusChangedHandler implements ApplicationEventHandler {
  readonly eventType = APPLICATION_EVENT_TYPE.BOOKING_STATUS_CHANGED;
  private readonly logger = new Logger(BookingStatusChangedHandler.name);

  handle(event: Readonly<ApplicationEvent<Record<string, unknown>>>): void {
    const p = event.payload as BookingStatusChangedPayload;
    this.logger.debug(
      `booking.status.changed bookingId=${p.bookingId} ${p.previousStatus}->${p.newStatus}`,
    );
  }
}
