import type { LlmClient } from '../llm.client';

/** Future: secondary provider / degraded mode implements {@link LlmClient}. */
export type FallbackLlmClient = LlmClient;
