import { Injectable } from '@nestjs/common';
import { IntegrationLoggingService } from '../../common/logging/integration-logging.service';

@Injectable()
export class TelegramIntegration {
  static readonly key = 'Telegram';

  constructor(private readonly log: IntegrationLoggingService) {}

  /** Planned: Telegram Bot API channel. */
  isPlanned(): boolean {
    this.log.logIntegrationRequest(TelegramIntegration.key, 'isPlanned', {});
    this.log.logIntegrationResponse(TelegramIntegration.key, 'isPlanned', {
      planned: true,
    });
    return true;
  }
}
