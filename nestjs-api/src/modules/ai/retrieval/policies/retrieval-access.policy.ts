/**
 * Priority: lower `order` on providers runs first (deterministic global ordering).
 */
export const RETRIEVAL_PROVIDER_ORDER = {
  STATIC_CATALOG: 10,
  SALON_CONFIG: 20,
  YCLIENTS_AVAILABILITY: 25,
  SCENARIO_METADATA: 30,
  DIALOG_SNAPSHOT: 40,
  RECENT_MESSAGES: 50,
  BOOKING_SUMMARIES: 60,
} as const;

/** Facts the model may treat as business context when present in the composed snapshot. */
export const ALLOWED_BUSINESS_FACT_CATEGORIES = [
  'salon display / branding labels from config',
  'static service category labels (not live inventory)',
  'YCLIENTS read-through cached services, staff, and availability snapshot (explicitly stale-aware; never invent slots beyond this slice)',
  'dialog identifiers and stage/status as loaded at retrieval time',
  'recent user/assistant message text as loaded at retrieval time',
  'scenario code string from request',
] as const;

export const FORBIDDEN_BUSINESS_CLAIMS = [
  'Live price lists, discounts, or promotions not in snapshot',
  'Appointment slot availability beyond what the yclients.availability snapshot lists when that slice is ok',
  'Staff schedules or internal KPIs beyond names listed in snapshot',
  'Anything inferred beyond provided facts',
] as const;

export const STALE_DATA_BEHAVIOR =
  'Snapshot fields reflect database state at retrieval time; they may be stale before inference — never imply real-time.';

export const UNAVAILABLE_DATA_BEHAVIOR =
  'If a slice is unavailable or empty, do not fabricate that category of information.';
