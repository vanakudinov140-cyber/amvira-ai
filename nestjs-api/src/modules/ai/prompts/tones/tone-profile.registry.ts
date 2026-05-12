import { Injectable } from '@nestjs/common';
import type { PromptBlock } from '../blocks/prompt-block.contract';
import { resolveToneProfile, type ToneProfileKey } from './tone-profiles';

/**
 * Selects tone blocks. Routing does not carry tone today — default profile;
 * optional scenario suffix may request neutral_concise via convention (documented).
 */
@Injectable()
export class ToneProfileRegistry {
  blocksFor(context: { scenarioCode?: string }): readonly PromptBlock[] {
    const key = this.resolveKey(context.scenarioCode);
    return resolveToneProfile(key).blocks;
  }

  toneKeyFor(context: { scenarioCode?: string }): ToneProfileKey {
    return this.resolveKey(context.scenarioCode) ?? 'professional_warm';
  }

  private resolveKey(scenarioCode?: string): ToneProfileKey | undefined {
    const s = scenarioCode?.toLowerCase() ?? '';
    if (s.includes('concise') || s.includes('neutral')) {
      return 'neutral_concise';
    }
    return undefined;
  }
}
