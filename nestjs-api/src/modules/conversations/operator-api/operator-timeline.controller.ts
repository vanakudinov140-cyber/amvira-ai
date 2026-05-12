import {
  Controller,
  Get,
  Param,
  ParseUUIDPipe,
  Query,
  UseFilters,
} from '@nestjs/common';
import { ApiOkResponse, ApiTags } from '@nestjs/swagger';
import { OperatorInboxQueryService } from '../inbox/operator-inbox-query.service';
import { OperatorApiExceptionFilter } from '../operator-http/operator-api-exception.filter';
import { OPERATOR_API_V1_PREFIX } from '../operator-http/operator-route.constants';
import { OperatorTimelineQueryDto } from '../operator-dto/operator-timeline-query.dto';
import { presentConversationTimeline } from '../operator-presenters/operator-timeline.presenter';

@ApiTags('operator')
@Controller(`${OPERATOR_API_V1_PREFIX}/timeline`)
@UseFilters(OperatorApiExceptionFilter)
export class OperatorTimelineController {
  constructor(private readonly inbox: OperatorInboxQueryService) {}

  @Get(':dialogId')
  @ApiOkResponse({ description: 'Conversation timeline read-model' })
  async getTimeline(
    @Param('dialogId', ParseUUIDPipe) dialogId: string,
    @Query() query: OperatorTimelineQueryDto,
  ) {
    const snapshot = await this.inbox.getConversationTimeline(dialogId);
    return presentConversationTimeline(snapshot, query.eventLimit);
  }
}
