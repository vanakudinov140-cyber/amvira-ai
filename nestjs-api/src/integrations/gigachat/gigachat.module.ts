import { Module } from '@nestjs/common';
import { GigachatIntegration } from './gigachat.integration';

@Module({
  providers: [GigachatIntegration],
  exports: [GigachatIntegration],
})
export class GigachatModule {}
