/**
 * Deterministic ordering of grounding fact keys for prompt composition.
 * Higher priority keys appear first in the serialized snapshot block.
 */
const PREFIX_PRIORITY: ReadonlyArray<readonly [string, number]> = [
  ['recent.messages', 100],
  ['booking.summaries', 90],
  ['yclients.availability', 85],
  ['dialog.snapshot', 70],
  ['scenario.metadata', 65],
  ['salon.config', 55],
  ['static.catalog', 20],
];

export function prioritizeRetrievalFactKeys(
  facts: Readonly<Record<string, unknown>>,
): readonly string[] {
  const keys = Object.keys(facts);
  const score = (k: string): number => {
    let s = 40;
    for (const [prefix, w] of PREFIX_PRIORITY) {
      if (k.startsWith(prefix)) {
        s = Math.max(s, w);
      }
    }
    if (k.includes('objection') || k.includes('booking')) {
      s += 5;
    }
    return s;
  };
  return [...keys].sort((a, b) => {
    const d = score(b) - score(a);
    if (d !== 0) {
      return d;
    }
    return a.localeCompare(b);
  });
}

export function orderedFactsJson(
  facts: Readonly<Record<string, unknown>>,
  orderedKeys: readonly string[],
  maxLen: number,
): string {
  const ordered: Record<string, unknown> = {};
  for (const k of orderedKeys) {
    if (k in facts) {
      ordered[k] = facts[k];
    }
  }
  const json = JSON.stringify(ordered);
  return json.length > maxLen ? `${json.slice(0, maxLen)}…[truncated]` : json;
}
