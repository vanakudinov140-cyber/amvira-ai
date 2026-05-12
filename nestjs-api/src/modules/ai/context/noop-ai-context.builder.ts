import { Injectable } from '@nestjs/common';
import { ALLOWED_FACT_SOURCE_KINDS } from '../domain/hallucination-boundaries';
import type {
  AiAssembledContext,
  AiContextAssemblyInput,
  AiContextBuilder,
} from './ai-context.builder';

@Injectable()
export class NoopAiContextBuilder implements AiContextBuilder {
  async build(input: AiContextAssemblyInput): Promise<AiAssembledContext> {
    return {
      dialogId: input.dialogId,
      correlationId: input.correlationId,
      currentStage: input.currentStage,
      dialogStatus: input.dialogStatus,
      channel: input.channel,
      scenarioCode: input.scenarioCode,
      userTurnText: input.userTurn?.text,
      allowedFactKeys: ['dialogId', 'currentStage', 'channel', 'scenarioCode'],
      allowedFactSources: [...ALLOWED_FACT_SOURCE_KINDS],
    };
  }
}
