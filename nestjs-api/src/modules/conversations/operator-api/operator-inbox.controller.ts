import {
  Body,
  Controller,
  Get,
  Param,
  ParseUUIDPipe,
  Post,
  Query,
  UseFilters,
} from '@nestjs/common';
import { ApiOkResponse, ApiTags } from '@nestjs/swagger';
import { OperatorInboxQueryService } from '../inbox/operator-inbox-query.service';
import { OperatorApiExceptionFilter } from '../operator-http/operator-api-exception.filter';
import { OPERATOR_API_V1_PREFIX } from '../operator-http/operator-route.constants';
import { OperatorInboxPreviewRequestDto } from '../operator-dto/operator-inbox-preview-request.dto';
import { OperatorInboxRowRequestDto, toOperatorInboxQueryInput } from '../operator-dto/operator-inbox-request.dto';
import { mapInboxPreviewContext } from '../operator-presenters/operator-inbox-preview.mapper';
import {
  presentOperatorInboxPreview,
  presentOperatorInboxRow,
} from '../operator-presenters/operator-inbox.presenter';

@ApiTags('operator')
@Controller(`${OPERATOR_API_V1_PREFIX}/inbox`)
@UseFilters(OperatorApiExceptionFilter)
export class OperatorInboxController {
  constructor(private readonly inbox: OperatorInboxQueryService) {}

  @Get(':dialogId')
  @ApiOkResponse({ description: 'Operator inbox row (minimal query context)' })
  async getRowMinimal(
    @Param('dialogId', ParseUUIDPipe) dialogId: string,
    @Query('takeoverActive') takeoverActive?: string,
  ) {
    const row = await this.inbox.getInboxRow({
      dialogId,
      workspaceSignals:
        takeoverActive === 'true'
          ? { takeoverActive: true }
          : takeoverActive === 'false'
            ? { takeoverActive: false }
            : undefined,
    });
    return presentOperatorInboxRow(row);
  }

  @Post('row')
  @ApiOkResponse({ description: 'Operator inbox row with optional workspace envelope' })
  async postRow(@Body() dto: OperatorInboxRowRequestDto) {
    const row = await this.inbox.getInboxRow(toOperatorInboxQueryInput(dto));
    return presentOperatorInboxRow(row);
  }

  @Post('preview')
  @ApiOkResponse({ description: 'Paged inbox preview for many dialogs' })
  async postPreview(@Body() dto: OperatorInboxPreviewRequestDto) {
    const offset = dto.offset ?? 0;
    const limit = dto.limit ?? 20;
    const total = dto.dialogIds.length;
    const slice = dto.dialogIds.slice(offset, offset + limit);
    const rows = await this.inbox.previewRows(
      slice,
      mapInboxPreviewContext(dto.contextByDialogId),
    );
    return presentOperatorInboxPreview(rows, { offset, limit, total });
  }
}
