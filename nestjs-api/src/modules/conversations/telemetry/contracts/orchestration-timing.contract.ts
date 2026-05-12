export type OrchestrationPhaseMarkV1 = {
  readonly phase: string;
  /** Milliseconds since orchestration turn wall-clock start. */
  readonly elapsedMs: number;
};

export type OrchestrationTimingV1 = {
  readonly timingVersion: 'orchestration_timing@v1';
  readonly marks: readonly OrchestrationPhaseMarkV1[];
  /** Wall time for AI suggest call only (when measured). */
  readonly aiSuggestWallMs?: number;
  readonly totalElapsedMs: number;
};
