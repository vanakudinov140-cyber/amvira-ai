import type { DeliveryReceipt } from '../../shared/integrations/delivery-receipt.contract';
import type { ChannelCapabilities } from './channel-capabilities.contract';
import type { ChannelOutboundMessage } from './channel-outbound-message.contract';

export const CHANNEL_ADAPTER = Symbol('CHANNEL_ADAPTER');

/**
 * User-facing channel port (Telegram, WhatsApp, …). No FSM, no Prisma models.
 */
export interface ChannelAdapter {
  readonly channelKey: string;
  readonly capabilities: ChannelCapabilities;
  deliver(message: ChannelOutboundMessage): Promise<DeliveryReceipt>;
}
