import { Injectable } from '@nestjs/common';
import type { LlmInvocationResponse } from '../contracts/llm.invocation';
import type { AiResponseValidator } from '../contracts/ai-response.validator';
import type { AssistantReplyStructuredV1 } from '../contracts/structured-output.contract';

@Injectable()
export class DefaultAiResponseValidator implements AiResponseValidator {
  validate(response: LlmInvocationResponse): AssistantReplyStructuredV1 | null {
    const text = response.rawText?.trim();
    if (!text) {
      return null;
    }
    try {
      const parsed: unknown = JSON.parse(text);
      if (!parsed || typeof parsed !== 'object') {
        return null;
      }
      const o = parsed as Record<string, unknown>;
      if (typeof o.replyText !== 'string' || typeof o.refused !== 'boolean') {
        return null;
      }
      const out: AssistantReplyStructuredV1 = {
        replyText: o.replyText,
        refused: o.refused,
        refusalReason:
          typeof o.refusalReason === 'string' ? o.refusalReason : undefined,
      };
      return out;
    } catch {
      return null;
    }
  }
}
