import { Module } from '@nestjs/common';
import { TelegramIntegration } from './telegram.integration';

@Module({
  providers: [TelegramIntegration],
  exports: [TelegramIntegration],
})
export class TelegramModule {}
