import { Inject, Injectable } from '@nestjs/common';
import type { AiGenerationRequest } from '../contracts/ai-generation.request';
import type { AiGenerationResult } from '../contracts/ai-generation.result';
import { AI_REFUSAL_REASON } from '../domain/ai-refusal.model';
import type { AiContextBuilder } from '../context/ai-context.builder';
import { AI_CONTEXT_BUILDER } from '../context/ai-context.builder';
import type { AiPromptComposer } from '../prompts/ai-prompt.composer';
import { AI_PROMPT_COMPOSER } from '../prompts/ai-prompt.composer';
import type { LlmClient } from '../contracts/llm.client';
import { LLM_CLIENT } from '../contracts/llm.client';
import type { LlmInvocationRequest } from '../contracts/llm.invocation';
import type { AiResponseValidator } from '../contracts/ai-response.validator';
import { AI_RESPONSE_VALIDATOR } from '../contracts/ai-response.validator';
import {
  ASSISTANT_REPLY_SCHEMA_ID,
  ASSISTANT_REPLY_SCHEMA_VERSION,
} from '../contracts/structured-output.contract';
import { AiPolicyEvaluator } from '../policies/ai-policy.evaluator';

/**
 * Orchestration skeleton: policy → context → prompt → LLM port → validation.
 * Does not touch FSM, repositories, application events, or persistence.
 */
@Injectable()
export class AiOrchestrationService {
  constructor(
    private readonly policy: AiPolicyEvaluator,
    @Inject(AI_CONTEXT_BUILDER)
    private readonly contextBuilder: AiContextBuilder,
    @Inject(AI_PROMPT_COMPOSER)
    private readonly promptComposer: AiPromptComposer,
    @Inject(LLM_CLIENT)
    private readonly llm: LlmClient,
    @Inject(AI_RESPONSE_VALIDATOR)
    private readonly responseValidator: AiResponseValidator,
  ) {}

  async suggest(request: AiGenerationRequest): Promise<AiGenerationResult> {
    const routing = this.policy.evaluate(request);
    if (!routing.allowed) {
      return {
        kind: 'refusal',
        refusal: {
          reason: routing.refusalReason,
          detail: routing.refusalDetail,
        },
      };
    }

    const context = await this.contextBuilder.build(request);
    const bundle = await this.promptComposer.compose(context, routing);

    const llmRequest: LlmInvocationRequest = {
      messages: [
        { role: 'system', content: bundle.systemSlot },
        { role: 'user', content: bundle.userSlot },
      ],
      temperature: routing.temperature,
      maxTokens: routing.maxTokens,
      correlationId: request.correlationId,
    };

    let raw;
    try {
      raw = await this.llm.generate(llmRequest);
    } catch {
      return {
        kind: 'failure',
        refusal: {
          reason: AI_REFUSAL_REASON.PROVIDER_UNAVAILABLE,
          detail: 'llm_client_threw',
        },
      };
    }

    const structured = this.responseValidator.validate(raw);
    if (!structured) {
      return {
        kind: 'failure',
        refusal: {
          reason: AI_REFUSAL_REASON.VALIDATION_FAILED,
          detail: 'response_shape',
        },
      };
    }

    if (structured.refused) {
      return {
        kind: 'refusal',
        refusal: {
          reason: AI_REFUSAL_REASON.CONTENT_FILTER,
          detail: structured.refusalReason ?? 'model_refusal',
        },
      };
    }

    return {
      kind: 'success',
      modelId: 'stub',
      structured: {
        schemaId: ASSISTANT_REPLY_SCHEMA_ID,
        schemaVersion: ASSISTANT_REPLY_SCHEMA_VERSION,
        data: structured as unknown as Record<string, unknown>,
      },
    };
  }
}
