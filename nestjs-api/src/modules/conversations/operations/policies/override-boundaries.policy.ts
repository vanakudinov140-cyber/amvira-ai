/**
 * Explicit boundaries: what AI proposals may imply vs what only operators may assert.
 */
export const AI_OVERRIDE_BOUNDARIES = {
  aiMaySuggestEscalation: true,
  aiMayNotAssignOperator: true,
  aiMayNotClearTakeover: true,
  aiMayNotCompleteEscalationTicket: true,
  operatorMaySuppressAssistantOutbound: true,
  operatorMayForceFsmTransitionViaExistingServices: true,
} as const;
