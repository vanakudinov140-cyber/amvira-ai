export function isIntentConfirmed(
  intentId: string,
  confirmed: ReadonlySet<string>,
): boolean {
  return confirmed.has(intentId);
}
