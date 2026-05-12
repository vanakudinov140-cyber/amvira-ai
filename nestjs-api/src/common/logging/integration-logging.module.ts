import { Global, Module } from '@nestjs/common';
import { IntegrationLoggingService } from './integration-logging.service';

@Global()
@Module({
  providers: [IntegrationLoggingService],
  exports: [IntegrationLoggingService],
})
export class IntegrationLoggingModule {}
