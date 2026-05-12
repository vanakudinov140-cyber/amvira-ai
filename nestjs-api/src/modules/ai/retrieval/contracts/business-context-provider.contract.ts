import type { BusinessRetrievalInput } from './business-retrieval-input.contract';
import type { BusinessRetrievalSlice } from './business-retrieval-slice.contract';

/**
 * Read-only business context slice. Side-effect free; no AI; no persistence.
 */
export interface BusinessContextProvider {
  readonly id: string;
  readonly scope: BusinessRetrievalSlice['scope'];
  /** Lower runs first (deterministic global ordering). */
  readonly order: number;
  retrieve(input: BusinessRetrievalInput): Promise<BusinessRetrievalSlice>;
}
