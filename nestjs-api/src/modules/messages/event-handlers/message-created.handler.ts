import { Injectable, Logger } from '@nestjs/common';
import type { ApplicationEvent } from '../../../shared/events/application-event';
import type { ApplicationEventHandler } from '../../../shared/events/application-event.handler';
import { APPLICATION_EVENT_TYPE } from '../../../shared/events/application-event-type';
import type { MessageCreatedPayload } from '../events/message-created.event';

@Injectable()
export class MessageCreatedHandler implements ApplicationEventHandler {
  readonly eventType = APPLICATION_EVENT_TYPE.MESSAGE_CREATED;
  private readonly logger = new Logger(MessageCreatedHandler.name);

  handle(event: Readonly<ApplicationEvent<Record<string, unknown>>>): void {
    const p = event.payload as MessageCreatedPayload;
    this.logger.debug(
      `message.created messageId=${p.messageId} dialogId=${p.dialogId} role=${p.role}`,
    );
  }
}
