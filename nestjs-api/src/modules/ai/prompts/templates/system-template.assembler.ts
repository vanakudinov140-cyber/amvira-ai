import { Injectable } from '@nestjs/common';
import type { PromptBlock, PromptBlockContext } from '../blocks/prompt-block.contract';

export type AssembledSystemPrompt = {
  readonly text: string;
  readonly blockIds: readonly string[];
};

/**
 * Linear template assembly — order is explicit in the composer, not data-driven.
 */
@Injectable()
export class SystemTemplateAssembler {
  assemble(blocks: readonly PromptBlock[], ctx: PromptBlockContext): AssembledSystemPrompt {
    const parts: string[] = [];
    const ids: string[] = [];
    for (const b of blocks) {
      const chunk = b.render(ctx).trim();
      if (chunk.length === 0) {
        continue;
      }
      parts.push(chunk);
      ids.push(b.id);
    }
    return {
      text: parts.join('\n\n'),
      blockIds: ids,
    };
  }
}
