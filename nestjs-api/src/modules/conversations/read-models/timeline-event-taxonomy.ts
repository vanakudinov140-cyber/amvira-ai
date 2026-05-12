/**
 * Stable timeline wire kinds — not Prisma enums and not LLM labels.
 *
 * Taxonomy (conceptual):
 * - **message.*** — utterances persisted as Message rows (user / assistant / system / tool).
 * - **dialog.state_snapshot** — synthetic read-model row: current funnel position + dialog status
 *   (not a replay of `DialogState` history; that would need a dedicated read API).
 */
export const TIMELINE_EVENT_KINDS = [
  'message.user',
  'message.assistant',
  'message.system',
  'message.tool',
  'dialog.state_snapshot',
] as const;

export type TimelineEventKind = (typeof TIMELINE_EVENT_KINDS)[number];

/**
 * Who produced the activity for operator UX filtering.
 * - **human** — end user text.
 * - **ai** — assistant model output.
 * - **system** — platform / lifecycle (snapshots, guards).
 * - **tool** — deterministic tool transcript rows when persisted as messages.
 */
export const TIMELINE_ACTOR_KINDS = ['human', 'ai', 'system', 'tool', 'unknown'] as const;

export type TimelineActorKind = (typeof TIMELINE_ACTOR_KINDS)[number];
