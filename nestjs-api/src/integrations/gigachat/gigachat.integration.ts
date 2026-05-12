import { Injectable } from '@nestjs/common';
import { IntegrationLoggingService } from '../../common/logging/integration-logging.service';

@Injectable()
export class GigachatIntegration {
  static readonly key = 'GigaChat';

  constructor(private readonly log: IntegrationLoggingService) {}

  /** Planned: generative text. Workflow and bookings remain in core services. */
  isPlanned(): boolean {
    this.log.logIntegrationRequest(GigachatIntegration.key, 'isPlanned', {});
    this.log.logIntegrationResponse(GigachatIntegration.key, 'isPlanned', {
      planned: true,
    });
    return true;
  }
}
