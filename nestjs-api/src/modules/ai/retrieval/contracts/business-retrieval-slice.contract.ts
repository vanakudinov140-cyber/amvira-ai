import type { RetrievalScope } from './retrieval-scope.contract';

/**
 * One provider contribution. Facts must be JSON-serializable plain data (no Prisma entities).
 */
export type BusinessRetrievalSlice = {
  readonly scope: RetrievalScope;
  readonly providerId: string;
  readonly order: number;
  readonly ok: boolean;
  readonly capturedAt: string;
  readonly unavailableReason?: string;
  /** Flat or nested plain values — composer may prefix keys by scope. */
  readonly facts: Readonly<Record<string, unknown>>;
};
