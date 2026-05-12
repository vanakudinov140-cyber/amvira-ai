/**
 * Central registry of application event type strings.
 * Naming: lower-case domain.entity.action (stable wire-style identifiers).
 */
export const APPLICATION_EVENT_TYPE = {
  DIALOG_CREATED: 'dialog.created',
  DIALOG_STAGE_TRANSITIONED: 'dialog.stage.transitioned',
  MESSAGE_CREATED: 'message.created',
  BOOKING_CREATED: 'booking.created',
  BOOKING_STATUS_CHANGED: 'booking.status.changed',
} as const;

export type ApplicationEventType =
  (typeof APPLICATION_EVENT_TYPE)[keyof typeof APPLICATION_EVENT_TYPE];
