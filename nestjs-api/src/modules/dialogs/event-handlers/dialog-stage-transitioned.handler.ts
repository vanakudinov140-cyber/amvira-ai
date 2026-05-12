import { Injectable, Logger } from '@nestjs/common';
import type { ApplicationEvent } from '../../../shared/events/application-event';
import type { ApplicationEventHandler } from '../../../shared/events/application-event.handler';
import { APPLICATION_EVENT_TYPE } from '../../../shared/events/application-event-type';
import type { DialogStageTransitionedPayload } from '../events/dialog-stage-transitioned.event';

@Injectable()
export class DialogStageTransitionedHandler implements ApplicationEventHandler {
  readonly eventType = APPLICATION_EVENT_TYPE.DIALOG_STAGE_TRANSITIONED;
  private readonly logger = new Logger(DialogStageTransitionedHandler.name);

  handle(event: Readonly<ApplicationEvent<Record<string, unknown>>>): void {
    const p = event.payload as DialogStageTransitionedPayload;
    this.logger.debug(
      `dialog.stage.transitioned dialogId=${p.dialogId} ${p.fromStage}->${p.toStage}`,
    );
  }
}
