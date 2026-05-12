export type GigachatErrorKind =
  | 'auth_failed'
  | 'http_error'
  | 'provider_error'
  | 'malformed_response'
  | 'timeout';

export class GigachatError extends Error {
  constructor(
    message: string,
    public readonly kind: GigachatErrorKind,
    public readonly retryable: boolean,
    public readonly httpStatus?: number,
    public readonly providerCode?: number,
  ) {
    super(message);
    this.name = 'GigachatError';
  }
}

export function isRetryableGigachatError(err: unknown): boolean {
  return err instanceof GigachatError && err.retryable === true;
}
