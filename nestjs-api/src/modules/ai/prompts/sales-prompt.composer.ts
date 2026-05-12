import { Injectable } from '@nestjs/common';
import type { AiAssembledContext } from '../context/ai-context.builder';
import type { AiRoutingAllowed } from '../policies/ai-policy.evaluator';
import type { AiPromptBundle, AiPromptComposer } from './ai-prompt.composer';
import { CORE_PIPELINE_PREFIX } from './blocks/core-identity.blocks';
import {
  BUSINESS_CONTEXT_SNAPSHOT_BLOCK,
  CONTEXT_SNAPSHOT_BLOCK,
  GROUNDING_BOUNDARIES_BLOCK,
} from './blocks/grounding.blocks';
import type { PromptBlock, PromptBlockContext } from './blocks/prompt-block.contract';
import { RESPONSE_CONSTRAINTS_BLOCK } from './blocks/response-constraints.block';
import {
  CONVERSATION_MEMORY_BLOCK,
  SALES_BEHAVIOR_CONSTRAINTS_BLOCK,
  SALES_PLAYBOOK_BLOCK,
} from './blocks/sales-playbook.blocks';
import {
  OBJECTION_PRIMITIVES_BLOCK,
  SALES_SCRIPT_BASE_BLOCK,
} from './blocks/sales-objection.blocks';
import {
  computePromptVersionHash,
  getPromptReleaseLabel,
} from './prompt-version.hash';
import { ScenarioPromptRegistry } from './scenarios/scenario-prompt.registry';
import { StagePromptRegistry } from './stages/stage-prompt.registry';
import { SystemTemplateAssembler } from './templates/system-template.assembler';
import { ToneProfileRegistry } from './tones/tone-profile.registry';

const OUTPUT_JSON_CONTRACT_BLOCK: PromptBlock = {
  id: 'output.json_contract',
  lane: 'system',
  render: () =>
    [
      'Output shape: reply only as JSON (no markdown code fences, no prose around it) with keys:',
      '- replyText: string (user-visible wording)',
      '- refused: boolean',
      '- refusalReason: optional string when refused is true',
    ].join('\n'),
};

@Injectable()
export class SalesPromptComposer implements AiPromptComposer {
  constructor(
    private readonly assembler: SystemTemplateAssembler,
    private readonly stages: StagePromptRegistry,
    private readonly scenarios: ScenarioPromptRegistry,
    private readonly tones: ToneProfileRegistry,
  ) {}

  async compose(
    context: AiAssembledContext,
    routing: AiRoutingAllowed,
  ): Promise<AiPromptBundle> {
    const ctx: PromptBlockContext = { context, routing };
    const blocks: PromptBlock[] = [
      ...CORE_PIPELINE_PREFIX,
      GROUNDING_BOUNDARIES_BLOCK,
      CONTEXT_SNAPSHOT_BLOCK,
      BUSINESS_CONTEXT_SNAPSHOT_BLOCK,
      CONVERSATION_MEMORY_BLOCK,
      SALES_PLAYBOOK_BLOCK,
      SALES_BEHAVIOR_CONSTRAINTS_BLOCK,
      ...this.stages.blocksFor(context.currentStage),
      ...this.scenarios.blocksFor(context.scenarioCode),
      ...this.tones.blocksFor(context),
      SALES_SCRIPT_BASE_BLOCK,
      OBJECTION_PRIMITIVES_BLOCK,
      RESPONSE_CONSTRAINTS_BLOCK,
      OUTPUT_JSON_CONTRACT_BLOCK,
    ];
    const assembled = this.assembler.assemble(blocks, ctx);
    const versionHash = computePromptVersionHash(assembled.blockIds);
    const userSlot = this.buildUserSlot(context);
    return {
      systemSlot: assembled.text,
      userSlot,
      trace: {
        promptVersion: getPromptReleaseLabel(),
        versionHash,
        stageKey: this.stages.strategyKey(context.currentStage),
        scenarioKey: this.scenarios.strategyKey(context.scenarioCode),
        toneKey: this.tones.toneKeyFor(context),
        blockIds: [...assembled.blockIds],
      },
    };
  }

  private buildUserSlot(context: AiAssembledContext): string {
    const text = context.userTurnText?.trim() ?? '';
    if (!text) {
      return '(no user message text in snapshot — produce a minimal safe reply or refuse with reason.)';
    }
    return `USER MESSAGE:\n${text}`;
  }
}
