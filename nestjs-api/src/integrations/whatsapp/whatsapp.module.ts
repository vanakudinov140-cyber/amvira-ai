import { Module } from '@nestjs/common';
import { WhatsappIntegration } from './whatsapp.integration';

@Module({
  providers: [WhatsappIntegration],
  exports: [WhatsappIntegration],
})
export class WhatsappModule {}
