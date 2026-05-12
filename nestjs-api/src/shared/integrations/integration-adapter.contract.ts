import type { IntegrationCommand } from './integration-command.contract';
import type { IntegrationSendResult } from './integration-send-result.contract';

export const INTEGRATION_ADAPTER = Symbol('INTEGRATION_ADAPTER');

/**
 * Single integration boundary (CRM, payments, …). No FSM, no Prisma types.
 * Implementations are transport-specific; not registered globally per key in this skeleton.
 */
export interface IntegrationAdapter {
  readonly integrationKey: string;
  send(command: IntegrationCommand): Promise<IntegrationSendResult>;
}
