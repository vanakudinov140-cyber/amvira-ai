export type YclientsErrorCode =
  | 'provider_unavailable'
  | 'auth_failure'
  | 'rate_limited'
  | 'invalid_payload'
  | 'slot_conflict'
  | 'stale_availability'
  | 'unknown';

export class YclientsIntegrationError extends Error {
  readonly code: YclientsErrorCode;
  readonly httpStatus?: number;
  readonly retryable: boolean;
  readonly correlationId?: string;

  constructor(
    message: string,
    opts: {
      readonly code: YclientsErrorCode;
      readonly httpStatus?: number;
      readonly retryable: boolean;
      readonly correlationId?: string;
    },
  ) {
    super(message);
    this.name = 'YclientsIntegrationError';
    this.code = opts.code;
    this.httpStatus = opts.httpStatus;
    this.retryable = opts.retryable;
    this.correlationId = opts.correlationId;
  }
}
