/**
 * Placeholder for future JWT / session subject — not persisted; transport-only.
 */
export type OperatorApiAuthContextPlaceholderV1 = {
  readonly contextVersion: 'operator_api_auth@v1';
  /** Opaque operator identity from gateway headers (optional). */
  readonly subject?: string;
  readonly displayLabel?: string;
};
