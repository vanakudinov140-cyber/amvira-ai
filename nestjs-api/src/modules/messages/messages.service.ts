import { Inject, Injectable } from '@nestjs/common';
import type { Message, Prisma } from '@prisma/client';
import { MessagesRepository } from '../../infrastructure/persistence/repositories/messages.repository';
import {
  APPLICATION_EVENT_PUBLISHER,
  type ApplicationEventPublisher,
} from '../../shared/events/application-event.publisher';
import { DialogsService } from '../dialogs/dialogs.service';
import { CreateMessageDto } from './dto/create-message.dto';
import { messageCreatedEvent } from './events/message-created.event';

@Injectable()
export class MessagesService {
  constructor(
    private readonly messages: MessagesRepository,
    private readonly dialogs: DialogsService,
    @Inject(APPLICATION_EVENT_PUBLISHER)
    private readonly applicationEvents: ApplicationEventPublisher,
  ) {}

  async createForDialog(
    dialogId: string,
    dto: CreateMessageDto,
  ): Promise<Message> {
    await this.dialogs.findOne(dialogId);
    const metadata = dto.metadata as Prisma.InputJsonValue | undefined;
    const message = await this.messages.create({
      dialog: { connect: { id: dialogId } },
      role: dto.role,
      content: dto.content,
      metadata,
    });

    this.applicationEvents.publish(
      messageCreatedEvent({
        id: message.id,
        dialogId: message.dialogId,
        role: message.role,
        createdAt: message.createdAt,
      }),
    );

    return message;
  }

  async listByDialog(dialogId: string): Promise<Message[]> {
    await this.dialogs.findOne(dialogId);
    return this.messages.findByDialogId(dialogId);
  }
}
