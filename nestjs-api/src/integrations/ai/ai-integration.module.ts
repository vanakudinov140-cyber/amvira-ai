import { Module } from '@nestjs/common';
import { AiCommunicationIntegration } from './ai-communication.integration';

@Module({
  providers: [AiCommunicationIntegration],
  exports: [AiCommunicationIntegration],
})
export class AiIntegrationModule {}
