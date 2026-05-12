import type { LlmInvocationRequest, LlmInvocationResponse } from './llm.invocation';

export const LLM_CLIENT = Symbol('LLM_CLIENT');

/**
 * LLM port — no HTTP, no SDK in this module. Implemented by stub or future adapters.
 */
export interface LlmClient {
  generate(request: LlmInvocationRequest): Promise<LlmInvocationResponse>;
}
