import { Controller, Get } from '@nestjs/common';
import { ApiOkResponse, ApiTags } from '@nestjs/swagger';
import { AppService } from './app.service';
import { HelloResponseDto } from './dto/hello-response.dto';

@ApiTags('app')
@Controller()
export class AppController {
  constructor(private readonly appService: AppService) {}

  @Get()
  @ApiOkResponse({ type: HelloResponseDto })
  async getHello(): Promise<HelloResponseDto> {
    return await this.appService.getHello();
  }
}
