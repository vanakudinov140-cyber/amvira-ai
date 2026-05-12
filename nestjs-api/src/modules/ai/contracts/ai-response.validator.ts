import type { LlmInvocationResponse } from './llm.invocation';
import type { AssistantReplyStructuredV1 } from './structured-output.contract';

export const AI_RESPONSE_VALIDATOR = Symbol('AI_RESPONSE_VALIDATOR');

export interface AiResponseValidator {
  validate(response: LlmInvocationResponse): AssistantReplyStructuredV1 | null;
}
