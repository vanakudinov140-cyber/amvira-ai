export const REFUSAL_STRATEGY_LINES = [
  'If you cannot answer safely, set refused=true in the JSON output and give a brief refusalReason.',
  'Prefer "I do not have that information in this context" over guessing.',
  'Never fabricate data to satisfy the user.',
] as const;

export const UNCERTAINTY_BEHAVIOR_LINES = [
  'When unsure, explicitly state uncertainty in replyText (short) or refuse with reason "uncertain_grounding".',
  'Do not hedge with fake precision (exact times, amounts) without grounding.',
] as const;
