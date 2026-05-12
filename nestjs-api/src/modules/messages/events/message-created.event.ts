import type { ApplicationEvent } from '../../../shared/events/application-event';
import { APPLICATION_EVENT_TYPE } from '../../../shared/events/application-event-type';

export type MessageCreatedPayload = {
  messageId: string;
  dialogId: string;
  role: string;
  createdAtIso: string;
};

export type MessageCreatedSource = {
  id: string;
  dialogId: string;
  role: string;
  createdAt: Date;
};

export function messageCreatedEvent(
  source: MessageCreatedSource,
): ApplicationEvent<MessageCreatedPayload> {
  return {
    type: APPLICATION_EVENT_TYPE.MESSAGE_CREATED,
    occurredAt: new Date(),
    payload: {
      messageId: source.id,
      dialogId: source.dialogId,
      role: source.role,
      createdAtIso: source.createdAt.toISOString(),
    },
  };
}
