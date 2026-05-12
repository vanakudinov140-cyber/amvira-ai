import type { AiRefusal } from '../domain/ai-refusal.model';
import type { StructuredAiEnvelope } from './structured-output.contract';

export type AiGenerationSuccess = {
  readonly kind: 'success';
  readonly modelId: string;
  readonly structured: StructuredAiEnvelope<Record<string, unknown>>;
};

export type AiGenerationRefusal = {
  readonly kind: 'refusal';
  readonly refusal: AiRefusal;
};

export type AiGenerationFailure = {
  readonly kind: 'failure';
  readonly refusal: AiRefusal;
};

export type AiGenerationResult =
  | AiGenerationSuccess
  | AiGenerationRefusal
  | AiGenerationFailure;
