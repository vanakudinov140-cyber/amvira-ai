import { Inject, Injectable } from '@nestjs/common';
import { WINSTON_MODULE_PROVIDER } from 'nest-winston';
import type { Logger } from 'winston';
import { LogEvent } from '../enums/log-event.enum';

export type StructuredLogPayload = Record<string, unknown>;

@Injectable()
export class IntegrationLoggingService {
  constructor(
    @Inject(WINSTON_MODULE_PROVIDER) private readonly logger: Logger,
  ) {}

  logIntegrationRequest(
    integration: string,
    operation: string,
    context?: StructuredLogPayload,
  ): void {
    this.logger.info({
      event: LogEvent.IntegrationRequest,
      integration,
      operation,
      ...context,
    });
  }

  logIntegrationResponse(
    integration: string,
    operation: string,
    context?: StructuredLogPayload,
  ): void {
    this.logger.info({
      event: LogEvent.IntegrationResponse,
      integration,
      operation,
      ...context,
    });
  }

  logAiRequest(context: StructuredLogPayload): void {
    this.logger.info({
      event: LogEvent.AiRequest,
      ...context,
    });
  }

  logAiResponse(context: StructuredLogPayload): void {
    this.logger.info({
      event: LogEvent.AiResponse,
      ...context,
    });
  }

  logError(message: string, context?: StructuredLogPayload): void {
    this.logger.error({
      event: LogEvent.ApplicationError,
      message,
      ...context,
    });
  }
}
