import { Injectable } from '@nestjs/common';
import type { DeliveryReceipt } from '../../shared/integrations/delivery-receipt.contract';
import type { ChannelAdapter } from './channel-adapter.contract';
import type { ChannelOutboundMessage } from './channel-outbound-message.contract';

@Injectable()
export class NoopChannelAdapter implements ChannelAdapter {
  readonly channelKey = 'noop';
  readonly capabilities = {
    maxBodyLength: 4096,
    supportsRichText: false,
    supportsButtons: false,
  } as const;

  async deliver(message: ChannelOutboundMessage): Promise<DeliveryReceipt> {
    return {
      idempotencyKey: message.idempotencyKey,
      deliveredAt: new Date(),
      channelKey: this.channelKey,
      status: 'ack',
      detail: 'noop_channel',
    };
  }
}
