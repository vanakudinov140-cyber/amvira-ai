import { Injectable } from '@nestjs/common';
import type { LlmClient } from './llm.client';
import type { LlmInvocationRequest, LlmInvocationResponse } from './llm.invocation';

/**
 * Deterministic stub — no network. Returns JSON-shaped text for validator tests.
 */
@Injectable()
export class StubLlmClient implements LlmClient {
  async generate(request: LlmInvocationRequest): Promise<LlmInvocationResponse> {
    const lastUser = [...request.messages].reverse().find((m) => m.role === 'user');
    const echoed = lastUser?.content?.slice(0, 200) ?? '';
    const payload = {
      replyText: echoed ? `[stub] ${echoed}` : '[stub]',
      refused: false,
    };
    return {
      rawText: JSON.stringify(payload),
      finishReason: 'stub',
    };
  }
}
