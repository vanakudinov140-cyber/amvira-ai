import {
  Body,
  Controller,
  Get,
  Param,
  ParseUUIDPipe,
  Patch,
  Post,
} from '@nestjs/common';
import { ApiCreatedResponse, ApiOkResponse, ApiTags } from '@nestjs/swagger';
import type { Dialog } from '@prisma/client';
import { DialogsService } from './dialogs.service';
import { CreateDialogDto } from './dto/create-dialog.dto';
import { TransitionDialogStageDto } from './dto/transition-dialog-stage.dto';

@ApiTags('dialogs')
@Controller('dialogs')
export class DialogsController {
  constructor(private readonly dialogsService: DialogsService) {}

  @Post()
  @ApiCreatedResponse({ description: 'Dialog created' })
  async create(@Body() dto: CreateDialogDto): Promise<Dialog> {
    return await this.dialogsService.create(dto);
  }

  @Get(':id')
  @ApiOkResponse({ description: 'Dialog by id' })
  async findOne(@Param('id', ParseUUIDPipe) id: string): Promise<Dialog> {
    return await this.dialogsService.findOne(id);
  }

  @Patch(':id/stage')
  @ApiOkResponse({
    description: 'Stage transitioned (business rules in service)',
  })
  async transitionStage(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: TransitionDialogStageDto,
  ): Promise<Dialog> {
    return await this.dialogsService.transitionStage(id, dto);
  }
}
