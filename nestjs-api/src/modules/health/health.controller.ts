import { Controller, Get } from '@nestjs/common';
import { ApiOkResponse, ApiTags } from '@nestjs/swagger';
import { HealthCheck } from '@nestjs/terminus';
import { HealthService } from './health.service';

@ApiTags('health')
@Controller('health')
export class HealthController {
  constructor(private readonly healthService: HealthService) {}

  @Get('live')
  @ApiOkResponse({ description: 'Liveness — process up (no external I/O)' })
  live() {
    return this.healthService.getLivePayload();
  }

  @Get('ready')
  @HealthCheck()
  @ApiOkResponse({ description: 'Readiness — postgres, redis, BullMQ (if enabled)' })
  ready() {
    return this.healthService.runReadyChecks();
  }

  @Get()
  @HealthCheck()
  @ApiOkResponse({ description: 'Alias for /health/ready (legacy probes)' })
  check() {
    return this.healthService.runReadyChecks();
  }
}
