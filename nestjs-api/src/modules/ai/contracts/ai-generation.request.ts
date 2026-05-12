/**
 * Application-level generation request. Funnel stage is read-only input only.
 */
export type AiGenerationRequest = {
  readonly dialogId: string;
  readonly correlationId?: string;
  /** Read-only funnel position — never mutated by AI layer. */
  readonly currentStage: string;
  readonly dialogStatus: string;
  readonly channel: string;
  readonly scenarioCode?: string;
  readonly userTurn?: {
    readonly text: string;
  };
};
