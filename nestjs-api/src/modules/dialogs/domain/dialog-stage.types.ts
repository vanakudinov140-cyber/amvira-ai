/**
 * Canonical funnel order for DialogStage (string codes mirror Prisma enum values).
 * Single backbone for forward index rules in dialog-stage.policy.ts.
 */
export const DIALOG_STAGE_ORDER = [
  'TRUST_BUILDING',
  'DISCOVERY',
  'PRESENTATION',
  'OBJECTION_HANDLING',
  'BOOKING',
  'COMPLETED',
] as const;

export type DialogStageCode = (typeof DIALOG_STAGE_ORDER)[number];

/**
 * Funnel terminal stages: no further forward progress along the backbone.
 * Outbound transitions are rejected except identity (handled in orchestration before policy).
 */
export const TERMINAL_FUNNEL_STAGES: readonly DialogStageCode[] = ['COMPLETED'];

/**
 * Runtime guard when bridging Prisma string enums into domain codes.
 */
export function isDialogStageCode(value: string): value is DialogStageCode {
  return (DIALOG_STAGE_ORDER as readonly string[]).includes(value);
}
