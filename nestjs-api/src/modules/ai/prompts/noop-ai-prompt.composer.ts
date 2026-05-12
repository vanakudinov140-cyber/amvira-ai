import { Injectable } from '@nestjs/common';
import type { AiAssembledContext } from '../context/ai-context.builder';
import type { AiRoutingAllowed } from '../policies/ai-policy.evaluator';
import type { AiPromptBundle, AiPromptComposer } from './ai-prompt.composer';

@Injectable()
export class NoopAiPromptComposer implements AiPromptComposer {
  async compose(
    context: AiAssembledContext,
    _routing: AiRoutingAllowed,
  ): Promise<AiPromptBundle> {
    return {
      systemSlot: `[placeholder] channel=${context.channel} stage=${context.currentStage} status=${context.dialogStatus}`,
      userSlot: context.userTurnText ?? '',
    };
  }
}
