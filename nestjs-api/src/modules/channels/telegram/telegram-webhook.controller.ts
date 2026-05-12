import {
  Body,
  Controller,
  Headers,
  Post,
  UnauthorizedException,
  UsePipes,
  ValidationPipe,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { ConversationOrchestratorService } from '../../conversations/use-cases/conversation-orchestrator.service';
import { TelegramUpdateMapper } from './telegram-update.mapper';
import { isTelegramTextMessageUpdate } from './telegram-update.validation';
import { TelegramWebhookSecretMismatchError } from './telegram.errors';

@Controller('channels/telegram')
@UsePipes(
  new ValidationPipe({
    whitelist: false,
    forbidUnknownValues: false,
    transform: false,
  }),
)
export class TelegramWebhookController {
  constructor(
    private readonly config: ConfigService,
    private readonly mapper: TelegramUpdateMapper,
    private readonly conversations: ConversationOrchestratorService,
  ) {}

  @Post('webhook')
  async webhook(
    @Headers('x-telegram-bot-api-secret-token') secretHeader: string | undefined,
    @Body() body: unknown,
  ): Promise<Record<string, unknown>> {
    const expected = this.config
      .get<string>('telegram.webhookSecretToken')
      ?.trim();
    if (expected) {
      if (secretHeader !== expected) {
        throw new UnauthorizedException(
          new TelegramWebhookSecretMismatchError().message,
        );
      }
    }

    if (!isTelegramTextMessageUpdate(body)) {
      return { ok: false, reason: 'invalid_or_unsupported_update' };
    }

    const mapped = this.mapper.toOrchestrationRequest(body);
    if (!mapped) {
      return { ok: false, reason: 'dialog_resolution_failed' };
    }

    const result = await this.conversations.handleUserMessage(mapped);
    return {
      ok: true,
      status: result.status,
      dialogId: result.dialogId,
      correlationId: result.correlationId,
    };
  }
}
