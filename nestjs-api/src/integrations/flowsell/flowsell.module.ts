import { Module } from '@nestjs/common';
import { FlowsellIntegration } from './flowsell.integration';

@Module({
  providers: [FlowsellIntegration],
  exports: [FlowsellIntegration],
})
export class FlowsellModule {}
