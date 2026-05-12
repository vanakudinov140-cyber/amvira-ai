import { Injectable } from '@nestjs/common';
import type { PromptBlock } from '../blocks/prompt-block.contract';

const STAGE_HINTS: Readonly<Record<string, string>> = {
  greet:
    'Stage hint (greeting): welcome briefly; invite the user to state their goal; no product claims.',
  qualify:
    'Stage hint (qualify): ask one focused clarifying question at a time; do not assume services.',
  propose:
    'Stage hint (propose): describe options in general terms only; tie to user-stated needs; no invented packages.',
  objection:
    'Stage hint (objection): acknowledge concern first; avoid arguing; no fabricated guarantees.',
  close:
    'Stage hint (close): confirm understanding; keep CTA soft; never confirm a booking yourself.',
  default:
    'Stage hint (general): stay helpful and grounded; follow user intent without inventing state.',
};

function normalizeStageToken(stage: string): string {
  const u = stage.toUpperCase();
  if (u.includes('GREET') || u.includes('OPEN')) {
    return 'greet';
  }
  if (u.includes('QUALIF') || u.includes('DISCOVER')) {
    return 'qualify';
  }
  if (u.includes('PROPOS') || u.includes('OFFER')) {
    return 'propose';
  }
  if (u.includes('OBJECTION') || u.includes('HANDLE')) {
    return 'objection';
  }
  if (u.includes('CLOSE') || u.includes('WIN')) {
    return 'close';
  }
  return 'default';
}

export function stageStrategyKey(stage: string): string {
  return normalizeStageToken(stage);
}

export function stageHintFor(stage: string): string {
  const key = normalizeStageToken(stage);
  return STAGE_HINTS[key] ?? STAGE_HINTS.default;
}

export function stagePromptBlocks(stage: string): readonly PromptBlock[] {
  const hint = stageHintFor(stage);
  return [
    {
      id: `stage.${stageStrategyKey(stage)}`,
      lane: 'system',
      render: () => hint,
    },
  ];
}

@Injectable()
export class StagePromptRegistry {
  strategyKey(stage: string): string {
    return stageStrategyKey(stage);
  }

  blocksFor(stage: string): readonly PromptBlock[] {
    return stagePromptBlocks(stage);
  }
}
