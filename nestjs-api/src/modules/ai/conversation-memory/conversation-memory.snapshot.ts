import type { SalonBusinessGroundingSnapshot } from '../retrieval/contracts/salon-grounding-snapshot.contract';

export type ConversationMemorySnapshotV1 = Readonly<{
  readonly snapshotVersion: 'conversation_memory@v1';
  readonly extractedPreferences: readonly string[];
  readonly preferredServices: readonly string[];
  readonly preferredStaff: readonly string[];
  readonly communicationTone: 'neutral' | 'warm' | 'formal' | 'brief';
  readonly priorObjectionCategories: readonly string[];
  readonly bookingHistorySummary: string;
  readonly missedBookingAttempts: number;
}>;

function getTurns(snapshot: SalonBusinessGroundingSnapshot | undefined): unknown {
  if (!snapshot) {
    return [];
  }
  const v = snapshot.facts['recent.messages/turns'];
  return Array.isArray(v) ? v : [];
}

function textFromTurns(turns: unknown): string {
  if (!Array.isArray(turns)) {
    return '';
  }
  return turns
    .map((t) => {
      if (!t || typeof t !== 'object') {
        return '';
      }
      const o = t as Record<string, unknown>;
      return typeof o.content === 'string' ? o.content : '';
    })
    .join('\n')
    .toLowerCase();
}

export function buildConversationMemorySnapshot(
  snapshot: SalonBusinessGroundingSnapshot | undefined,
): ConversationMemorySnapshotV1 {
  const turns = getTurns(snapshot);
  const blob = textFromTurns(turns);

  const prefs: string[] = [];
  if (blob.includes('аллерг')) {
    prefs.push('mentions_allergy_sensitivity');
  }
  if (blob.includes('вечер') || blob.includes('утро')) {
    prefs.push('time_of_day_preference_signal');
  }

  const services: string[] = [];
  const svcFacts = snapshot?.facts['yclients.availability/availableServices'];
  if (Array.isArray(svcFacts)) {
    for (const row of svcFacts) {
      if (row && typeof row === 'object' && 'title' in row) {
        const t = (row as { title?: unknown }).title;
        if (typeof t === 'string') {
          services.push(t);
        }
      }
    }
  }
  const preferredServices = services.filter((s) =>
    blob.includes(s.toLowerCase().slice(0, 12)),
  );

  const staff: string[] = [];
  const staffFacts = snapshot?.facts['yclients.availability/staffNames'];
  if (Array.isArray(staffFacts)) {
    for (const row of staffFacts) {
      if (row && typeof row === 'object' && 'name' in row) {
        const n = (row as { name?: unknown }).name;
        if (typeof n === 'string') {
          staff.push(n);
        }
      }
    }
  }
  const preferredStaff = staff.filter((n) =>
    blob.includes(n.toLowerCase().slice(0, 8)),
  );

  let tone: ConversationMemorySnapshotV1['communicationTone'] = 'neutral';
  if (blob.includes('спасибо') || blob.includes('🙂') || blob.includes('❤')) {
    tone = 'warm';
  }
  if (blob.length > 0 && blob.length < 120 && !blob.includes('?')) {
    tone = 'brief';
  }
  if (blob.includes('здравствуйте') || blob.includes('уважаем')) {
    tone = 'formal';
  }

  const objections: string[] = [];
  const pairs: ReadonlyArray<[string, string]> = [
    ['price', 'дорог'],
    ['trust', 'довер'],
    ['timing', 'потом'],
    ['hesitation', 'не уверен'],
    ['comparison', 'другой салон'],
  ];
  for (const [cat, needle] of pairs) {
    if (blob.includes(needle)) {
      objections.push(cat);
    }
  }

  let bookingSummary = 'no_confirmed_booking_rows_in_retrieval';
  const sums = snapshot?.facts['booking.summaries/summaries'];
  if (Array.isArray(sums) && sums.length > 0) {
    bookingSummary = `booking_rows:${sums.length}`;
  }

  let missed = 0;
  if (blob.includes('запис') && blob.includes('не могу')) {
    missed += 1;
  }
  if (blob.includes('слот') && blob.includes('занят')) {
    missed += 1;
  }

  return {
    snapshotVersion: 'conversation_memory@v1',
    extractedPreferences: prefs,
    preferredServices: [...new Set(preferredServices)].slice(0, 5),
    preferredStaff: [...new Set(preferredStaff)].slice(0, 5),
    communicationTone: tone,
    priorObjectionCategories: [...new Set(objections)].slice(0, 5),
    bookingHistorySummary: bookingSummary,
    missedBookingAttempts: missed,
  };
}
