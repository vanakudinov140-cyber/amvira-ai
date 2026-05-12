import type { ApplicationEvent } from '../../../shared/events/application-event';
import { APPLICATION_EVENT_TYPE } from '../../../shared/events/application-event-type';

export type DialogStageTransitionedPayload = {
  dialogId: string;
  clientId: string;
  scenarioId: string;
  fromStage: string;
  toStage: string;
};

export function dialogStageTransitionedEvent(
  payload: DialogStageTransitionedPayload,
): ApplicationEvent<DialogStageTransitionedPayload> {
  return {
    type: APPLICATION_EVENT_TYPE.DIALOG_STAGE_TRANSITIONED,
    occurredAt: new Date(),
    payload: { ...payload },
  };
}
