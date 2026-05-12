import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ConversationsModule } from '../../conversations/conversations.module';
import { TelegramChannelAdapter } from './telegram-channel.adapter';
import { TelegramUpdateMapper } from './telegram-update.mapper';
import { TelegramWebhookController } from './telegram-webhook.controller';
import { TelegramWebhookBootstrapService } from './telegram-webhook.bootstrap';

@Module({
  imports: [ConfigModule, ConversationsModule],
  controllers: [TelegramWebhookController],
  providers: [
    TelegramChannelAdapter,
    TelegramUpdateMapper,
    TelegramWebhookBootstrapService,
  ],
  exports: [TelegramChannelAdapter],
})
export class TelegramChannelModule {}
