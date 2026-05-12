import { Global, Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import type { ChannelAdapter } from './channel-adapter.contract';
import { CHANNEL_ADAPTER } from './channel-adapter.contract';
import { NoopChannelAdapter } from './noop-channel.adapter';
import { TelegramChannelModule } from './telegram/telegram-channel.module';
import { TelegramChannelAdapter } from './telegram/telegram-channel.adapter';

@Global()
@Module({
  imports: [ConfigModule, TelegramChannelModule],
  providers: [
    NoopChannelAdapter,
    {
      provide: CHANNEL_ADAPTER,
      useFactory: (
        config: ConfigService,
        telegram: TelegramChannelAdapter,
        noop: NoopChannelAdapter,
      ): ChannelAdapter => {
        const token = config.get<string>('telegram.botToken')?.trim();
        return token ? telegram : noop;
      },
      inject: [ConfigService, TelegramChannelAdapter, NoopChannelAdapter],
    },
  ],
  exports: [CHANNEL_ADAPTER, NoopChannelAdapter, TelegramChannelModule],
})
export class ChannelsModule {}
