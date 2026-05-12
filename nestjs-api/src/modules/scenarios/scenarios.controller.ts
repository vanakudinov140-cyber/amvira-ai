import { Controller, Get } from '@nestjs/common';
import { ApiOkResponse, ApiTags } from '@nestjs/swagger';
import type { Scenario } from '@prisma/client';
import { ScenariosService } from './scenarios.service';

@ApiTags('scenarios')
@Controller('scenarios')
export class ScenariosController {
  constructor(private readonly scenariosService: ScenariosService) {}

  @Get()
  @ApiOkResponse({ description: 'Active consultation scenarios' })
  async findActive(): Promise<Scenario[]> {
    return await this.scenariosService.findActive();
  }
}
