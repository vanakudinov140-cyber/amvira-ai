import { Injectable } from '@nestjs/common';
import type { AiGenerationRequest } from '../contracts/ai-generation.request';
import { AI_REFUSAL_REASON, type AiRefusalReason } from '../domain/ai-refusal.model';

export type AiPolicyInput = Readonly<
  Pick<
    AiGenerationRequest,
    'dialogId' | 'currentStage' | 'dialogStatus' | 'channel' | 'scenarioCode'
  >
>;

export type AiRoutingDecision =
  | {
      readonly allowed: true;
      readonly temperature: number;
      readonly maxTokens: number;
    }
  | {
      readonly allowed: false;
      readonly refusalReason: AiRefusalReason;
      readonly refusalDetail: string;
    };

export type AiRoutingAllowed = Extract<AiRoutingDecision, { allowed: true }>;

@Injectable()
export class AiPolicyEvaluator {
  evaluate(input: AiPolicyInput): AiRoutingDecision {
    if (input.dialogStatus === 'CLOSED') {
      return {
        allowed: false,
        refusalReason: AI_REFUSAL_REASON.POLICY_DENIED,
        refusalDetail: 'dialog_closed',
      };
    }
    return {
      allowed: true,
      temperature: 0.3,
      maxTokens: 512,
    };
  }
}
