import {
  Body,
  Controller,
  Get,
  Param,
  ParseUUIDPipe,
  Post,
} from '@nestjs/common';
import { ApiCreatedResponse, ApiOkResponse, ApiTags } from '@nestjs/swagger';
import type { Message } from '@prisma/client';
import { CreateMessageDto } from './dto/create-message.dto';
import { MessagesService } from './messages.service';

@ApiTags('messages')
@Controller('dialogs/:dialogId/messages')
export class MessagesController {
  constructor(private readonly messagesService: MessagesService) {}

  @Post()
  @ApiCreatedResponse({ description: 'Message stored for dialog' })
  async create(
    @Param('dialogId', ParseUUIDPipe) dialogId: string,
    @Body() dto: CreateMessageDto,
  ): Promise<Message> {
    return await this.messagesService.createForDialog(dialogId, dto);
  }

  @Get()
  @ApiOkResponse({ description: 'Messages for dialog' })
  async list(
    @Param('dialogId', ParseUUIDPipe) dialogId: string,
  ): Promise<Message[]> {
    return await this.messagesService.listByDialog(dialogId);
  }
}
