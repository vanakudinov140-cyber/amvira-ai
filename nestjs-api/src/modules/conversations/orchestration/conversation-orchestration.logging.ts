import { Injectable, Logger } from '@nestjs/common';

export type ConversationOrchestrationLogPhase =
  | 'start'
  | 'dialog_loaded'
  | 'dialog_guard'
  | 'user_persist'
  | 'ai_suggest'
  | 'ai_structured_validate'
  | 'assistant_persist'
  | 'channel_dispatch'
  | 'async_dispatch'
  | 'idempotency_hit'
  | 'complete';

/**
 * Nest Logger + JSON payloads — no external logging SDK.
 */
@Injectable()
export class ConversationOrchestrationLogger {
  private readonly logger = new Logger(ConversationOrchestrationLogger.name);

  logStructured(
    phase: ConversationOrchestrationLogPhase,
    fields: Record<string, unknown>,
  ): void {
    this.logger.log(JSON.stringify({ phase, ...fields }));
  }

  warnStructured(
    phase: ConversationOrchestrationLogPhase,
    fields: Record<string, unknown>,
  ): void {
    this.logger.warn(JSON.stringify({ phase, ...fields }));
  }

  errorStructured(
    phase: ConversationOrchestrationLogPhase,
    fields: Record<string, unknown>,
  ): void {
    this.logger.error(JSON.stringify({ phase, ...fields }));
  }
}
