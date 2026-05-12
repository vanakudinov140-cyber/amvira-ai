import { Injectable } from '@nestjs/common';
import type { IntegrationAdapter } from '../../shared/integrations/integration-adapter.contract';
import type { IntegrationCommand } from '../../shared/integrations/integration-command.contract';
import type { IntegrationSendResult } from '../../shared/integrations/integration-send-result.contract';

@Injectable()
export class NoopIntegrationAdapter implements IntegrationAdapter {
  readonly integrationKey = 'noop';

  async send(command: IntegrationCommand): Promise<IntegrationSendResult> {
    return {
      ok: true,
      detail: 'noop_integration',
      externalId: command.idempotencyKey,
    };
  }
}
