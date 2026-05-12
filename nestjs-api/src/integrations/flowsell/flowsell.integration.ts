import { Injectable } from '@nestjs/common';
import { IntegrationLoggingService } from '../../common/logging/integration-logging.service';

@Injectable()
export class FlowsellIntegration {
  static readonly key = 'FlowSell';

  constructor(private readonly log: IntegrationLoggingService) {}

  /** Planned: CRM / funnel automation. */
  isPlanned(): boolean {
    this.log.logIntegrationRequest(FlowsellIntegration.key, 'isPlanned', {});
    this.log.logIntegrationResponse(FlowsellIntegration.key, 'isPlanned', {
      planned: true,
    });
    return true;
  }
}
