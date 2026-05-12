/**
 * Injected by channel / operator API — never synthesized from model text alone.
 */
export type OperatorOrchestrationContextV1 = {
  readonly contextVersion: 'operator_orchestration_context@v1';
  readonly operatorTakeoverActive?: boolean;
  readonly resumeAssistantRequested?: boolean;
  /**
   * Explicit operator or control-plane ack to materialize queue routing for this turn.
   * AI outputs must not flip this flag.
   */
  readonly confirmEscalationToQueue?: boolean;
};
