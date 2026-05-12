import { Injectable, Logger } from '@nestjs/common';
import type { TelemetryStructuredEventV1 } from './contracts/telemetry-structured-event.contract';

export const CONVERSATION_TELEMETRY_PUBLISHER = Symbol(
  'CONVERSATION_TELEMETRY_PUBLISHER',
);

export interface ConversationTelemetryPublisher {
  publishStructured(event: TelemetryStructuredEventV1): void;
}

@Injectable()
export class LoggerConversationTelemetryPublisher
  implements ConversationTelemetryPublisher
{
  private readonly logger = new Logger(LoggerConversationTelemetryPublisher.name);

  publishStructured(event: TelemetryStructuredEventV1): void {
    const emit = (): void => {
      try {
        this.logger.log(JSON.stringify(event));
      } catch {
        /* telemetry must never break orchestration */
      }
    };
    if (typeof setImmediate === 'function') {
      setImmediate(emit);
    } else {
      void Promise.resolve().then(emit);
    }
  }
}
