import { Injectable } from '@nestjs/common';
import type { BusinessContextProvider } from './contracts/business-context-provider.contract';
import type { BusinessRetrievalInput } from './contracts/business-retrieval-input.contract';
import type { BusinessRetrievalSlice } from './contracts/business-retrieval-slice.contract';
import type {
  BusinessRetrievalTrace,
  SalonBusinessGroundingSnapshot,
} from './contracts/salon-grounding-snapshot.contract';
import { GroundingSnapshotComposer } from './snapshots/grounding-snapshot.composer';
import { BookingSummariesBusinessContextProvider } from './providers/booking-summaries.business-context.provider';
import { DialogSnapshotBusinessContextProvider } from './providers/dialog-snapshot.business-context.provider';
import { RecentMessagesBusinessContextProvider } from './providers/recent-messages.business-context.provider';
import { SalonConfigBusinessContextProvider } from './providers/salon-config.business-context.provider';
import { ScenarioSnapshotBusinessContextProvider } from './providers/scenario-snapshot.business-context.provider';
import { StaticCatalogBusinessContextProvider } from './providers/static-catalog.business-context.provider';
import { YclientsAvailabilityBusinessContextProvider } from './providers/yclients-availability.business-context.provider';

@Injectable()
export class BusinessContextRetrievalService {
  private readonly providers: readonly BusinessContextProvider[];

  constructor(
    private readonly composer: GroundingSnapshotComposer,
    pStatic: StaticCatalogBusinessContextProvider,
    pSalon: SalonConfigBusinessContextProvider,
    pYclients: YclientsAvailabilityBusinessContextProvider,
    pScenario: ScenarioSnapshotBusinessContextProvider,
    pDialog: DialogSnapshotBusinessContextProvider,
    pMessages: RecentMessagesBusinessContextProvider,
    pBooking: BookingSummariesBusinessContextProvider,
  ) {
    this.providers = [
      pStatic,
      pSalon,
      pYclients,
      pScenario,
      pDialog,
      pMessages,
      pBooking,
    ].sort((a, b) => a.order - b.order);
  }

  async retrieve(
    input: BusinessRetrievalInput,
  ): Promise<SalonBusinessGroundingSnapshot> {
    const slices: BusinessRetrievalSlice[] = [];
    const traceRows: BusinessRetrievalTrace['providers'][number][] = [];
    const traceStart = new Date().toISOString();
    for (const p of this.providers) {
      const t0 = Date.now();
      try {
        const slice = await p.retrieve(input);
        slices.push(slice);
        traceRows.push({
          providerId: slice.providerId,
          scope: slice.scope,
          order: p.order,
          ok: slice.ok,
          durationMs: Date.now() - t0,
          unavailableReason: slice.unavailableReason,
        });
      } catch {
        const fallback: BusinessRetrievalSlice = {
          scope: p.scope,
          providerId: p.id,
          order: p.order,
          ok: false,
          capturedAt: new Date().toISOString(),
          unavailableReason: 'provider_threw',
          facts: {},
        };
        slices.push(fallback);
        traceRows.push({
          providerId: p.id,
          scope: p.scope,
          order: p.order,
          ok: false,
          durationMs: Date.now() - t0,
          unavailableReason: 'provider_threw',
        });
      }
    }
    const trace: BusinessRetrievalTrace = {
      capturedAt: traceStart,
      providers: traceRows,
    };
    return this.composer.compose(slices, trace);
  }
}
