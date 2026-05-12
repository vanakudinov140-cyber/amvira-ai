import { Global, Module } from '@nestjs/common';
import { BookingCreatedHandler } from '../../modules/bookings/event-handlers/booking-created.handler';
import { BookingStatusChangedHandler } from '../../modules/bookings/event-handlers/booking-status-changed.handler';
import { DialogCreatedHandler } from '../../modules/dialogs/event-handlers/dialog-created.handler';
import { DialogStageTransitionedHandler } from '../../modules/dialogs/event-handlers/dialog-stage-transitioned.handler';
import { MessageCreatedHandler } from '../../modules/messages/event-handlers/message-created.handler';
import {
  APPLICATION_EVENT_HANDLERS,
  ApplicationEventHandlerRegistry,
} from './application-event-handler.registry';
import type { ApplicationEventHandler } from './application-event.handler';
import { APPLICATION_EVENT_PUBLISHER } from './application-event.publisher';
import { InMemoryApplicationEventPublisher } from './in-memory-event.publisher';

@Global()
@Module({
  providers: [
    InMemoryApplicationEventPublisher,
    {
      provide: APPLICATION_EVENT_PUBLISHER,
      useExisting: InMemoryApplicationEventPublisher,
    },
    DialogCreatedHandler,
    DialogStageTransitionedHandler,
    MessageCreatedHandler,
    BookingCreatedHandler,
    BookingStatusChangedHandler,
    {
      provide: APPLICATION_EVENT_HANDLERS,
      useFactory: (
        dialogCreated: DialogCreatedHandler,
        dialogStageTransitioned: DialogStageTransitionedHandler,
        messageCreated: MessageCreatedHandler,
        bookingCreated: BookingCreatedHandler,
        bookingStatusChanged: BookingStatusChangedHandler,
      ): ApplicationEventHandler[] => [
        dialogCreated,
        dialogStageTransitioned,
        messageCreated,
        bookingCreated,
        bookingStatusChanged,
      ],
      inject: [
        DialogCreatedHandler,
        DialogStageTransitionedHandler,
        MessageCreatedHandler,
        BookingCreatedHandler,
        BookingStatusChangedHandler,
      ],
    },
    ApplicationEventHandlerRegistry,
  ],
  exports: [
    APPLICATION_EVENT_PUBLISHER,
    InMemoryApplicationEventPublisher,
  ],
})
export class ApplicationEventsModule {}
