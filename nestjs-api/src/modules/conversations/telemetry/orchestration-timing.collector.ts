import { performance } from 'node:perf_hooks';
import type {
  OrchestrationPhaseMarkV1,
  OrchestrationTimingV1,
} from './contracts/orchestration-timing.contract';

export class OrchestrationTimingCollector {
  private readonly monoStart = performance.now();
  private readonly marks: OrchestrationPhaseMarkV1[] = [];
  private aiSuggestWallMs?: number;

  mark(phase: string): void {
    this.marks.push({
      phase,
      elapsedMs: Math.round(performance.now() - this.monoStart),
    });
  }

  setAiSuggestWallMs(ms: number): void {
    this.aiSuggestWallMs = ms;
  }

  build(): OrchestrationTimingV1 {
    return {
      timingVersion: 'orchestration_timing@v1',
      marks: [...this.marks],
      aiSuggestWallMs: this.aiSuggestWallMs,
      totalElapsedMs: Math.round(performance.now() - this.monoStart),
    };
  }
}
