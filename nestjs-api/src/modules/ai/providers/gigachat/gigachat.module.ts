import { Module } from '@nestjs/common';
import { GigachatAuthService } from './gigachat-auth.service';
import { GigachatLlmClient } from './gigachat-llm.client';

@Module({
  providers: [GigachatAuthService, GigachatLlmClient],
  exports: [GigachatAuthService, GigachatLlmClient],
})
export class GigachatProviderModule {}
