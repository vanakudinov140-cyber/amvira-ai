import { Body, Controller, Post, UseFilters } from '@nestjs/common';
import { ApiOkResponse, ApiTags } from '@nestjs/swagger';
import { OperatorActionOrchestratorService } from '../operator-actions/operator-action-orchestrator.service';
import { OperatorApiExceptionFilter } from '../operator-http/operator-api-exception.filter';
import { OPERATOR_API_V1_PREFIX } from '../operator-http/operator-route.constants';
import {
  ExecuteOperatorActionDto,
  toOperatorCommandEnvelope,
} from '../operator-dto/operator-action-request.dto';
import { presentOperatorActionResult } from '../operator-presenters/operator-action.presenter';

@ApiTags('operator')
@Controller(`${OPERATOR_API_V1_PREFIX}/actions`)
@UseFilters(OperatorApiExceptionFilter)
export class OperatorActionsController {
  constructor(private readonly operatorActions: OperatorActionOrchestratorService) {}

  @Post('execute')
  @ApiOkResponse({ description: 'Execute operator command envelope' })
  async execute(@Body() dto: ExecuteOperatorActionDto) {
    const envelope = toOperatorCommandEnvelope(dto);
    const result = await this.operatorActions.execute(envelope);
    return presentOperatorActionResult(result);
  }
}
