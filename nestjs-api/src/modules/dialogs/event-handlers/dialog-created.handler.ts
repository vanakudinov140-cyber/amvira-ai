import { Injectable, Logger } from '@nestjs/common';
import type { ApplicationEvent } from '../../../shared/events/application-event';
import type { ApplicationEventHandler } from '../../../shared/events/application-event.handler';
import { APPLICATION_EVENT_TYPE } from '../../../shared/events/application-event-type';
import type { DialogCreatedPayload } from '../events/dialog-created.event';

@Injectable()
export class DialogCreatedHandler implements ApplicationEventHandler {
  readonly eventType = APPLICATION_EVENT_TYPE.DIALOG_CREATED;
  private readonly logger = new Logger(DialogCreatedHandler.name);

  handle(event: Readonly<ApplicationEvent<Record<string, unknown>>>): void {
    const p = event.payload as DialogCreatedPayload;
    this.logger.debug(
      `dialog.created dialogId=${p.dialogId} clientId=${p.clientId} scenarioId=${p.scenarioId} channel=${p.channel} stage=${p.initialStage}`,
    );
  }
}
