import type { ApplicationEvent } from '../../../shared/events/application-event';
import { APPLICATION_EVENT_TYPE } from '../../../shared/events/application-event-type';

export type DialogCreatedPayload = {
  dialogId: string;
  clientId: string;
  scenarioId: string;
  channel: string;
  initialStage: string;
  status: string;
};

/** Narrow projection — do not pass Prisma `Dialog` here. */
export type DialogCreatedSource = {
  id: string;
  clientId: string;
  scenarioId: string;
  channel: string;
  currentStage: string;
  status: string;
};

export function dialogCreatedEvent(
  source: DialogCreatedSource,
): ApplicationEvent<DialogCreatedPayload> {
  return {
    type: APPLICATION_EVENT_TYPE.DIALOG_CREATED,
    occurredAt: new Date(),
    payload: {
      dialogId: source.id,
      clientId: source.clientId,
      scenarioId: source.scenarioId,
      channel: source.channel,
      initialStage: source.currentStage,
      status: source.status,
    },
  };
}
