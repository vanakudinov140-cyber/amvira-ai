import { Injectable } from '@nestjs/common';
import { IntegrationLoggingService } from '../../common/logging/integration-logging.service';

@Injectable()
export class WhatsappIntegration {
  static readonly key = 'WhatsApp';

  constructor(private readonly log: IntegrationLoggingService) {}

  /** Planned: WhatsApp Business channel. */
  isPlanned(): boolean {
    this.log.logIntegrationRequest(WhatsappIntegration.key, 'isPlanned', {});
    this.log.logIntegrationResponse(WhatsappIntegration.key, 'isPlanned', {
      planned: true,
    });
    return true;
  }
}
