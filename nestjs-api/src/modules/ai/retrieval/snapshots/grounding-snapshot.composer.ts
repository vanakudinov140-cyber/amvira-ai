import { Injectable } from '@nestjs/common';
import type { BusinessRetrievalSlice } from '../contracts/business-retrieval-slice.contract';
import type {
  BusinessRetrievalTrace,
  SalonBusinessGroundingSnapshot,
} from '../contracts/salon-grounding-snapshot.contract';

function prefixFacts(
  scope: string,
  facts: Readonly<Record<string, unknown>>,
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(facts)) {
    out[`${scope}/${k}`] = v;
  }
  return out;
}

@Injectable()
export class GroundingSnapshotComposer {
  compose(
    slices: readonly BusinessRetrievalSlice[],
    trace: BusinessRetrievalTrace,
  ): SalonBusinessGroundingSnapshot {
    const merged: Record<string, unknown> = {};
    for (const s of slices) {
      if (!s.ok || Object.keys(s.facts).length === 0) {
        continue;
      }
      Object.assign(merged, prefixFacts(s.scope, s.facts));
    }
    return {
      snapshotVersion: 'salon.grounding.v1',
      facts: merged,
      trace,
    };
  }
}
