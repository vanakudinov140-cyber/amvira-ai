import type { RetrievalScope } from './retrieval-scope.contract';

export type RetrievalProviderTrace = {
  readonly providerId: string;
  readonly scope: RetrievalScope;
  readonly order: number;
  readonly ok: boolean;
  readonly durationMs: number;
  readonly unavailableReason?: string;
};

export type BusinessRetrievalTrace = {
  readonly capturedAt: string;
  readonly providers: readonly RetrievalProviderTrace[];
};

/**
 * Composed read-only view for grounding — not memory, not inferred truth.
 */
export type SalonBusinessGroundingSnapshot = {
  readonly snapshotVersion: 'salon.grounding.v1';
  readonly facts: Readonly<Record<string, unknown>>;
  readonly trace: BusinessRetrievalTrace;
};
