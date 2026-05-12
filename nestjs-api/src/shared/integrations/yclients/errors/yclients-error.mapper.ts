import { YclientsIntegrationError } from './yclients-integration.error';
import type { YclientsErrorCode } from './yclients-integration.error';

export function classifyYclientsHttpFailure(input: {
  readonly status: number;
  readonly bodyText?: string;
  readonly correlationId?: string;
}): YclientsIntegrationError {
  const { status, bodyText, correlationId } = input;
  if (status === 401 || status === 403) {
    return new YclientsIntegrationError('YCLIENTS auth rejected', {
      code: 'auth_failure',
      httpStatus: status,
      retryable: false,
      correlationId,
    });
  }
  if (status === 429) {
    return new YclientsIntegrationError('YCLIENTS rate limited', {
      code: 'rate_limited',
      httpStatus: status,
      retryable: true,
      correlationId,
    });
  }
  if (status === 409) {
    return new YclientsIntegrationError('YCLIENTS slot conflict', {
      code: 'slot_conflict',
      httpStatus: status,
      retryable: false,
      correlationId,
    });
  }
  if (status === 400 || status === 422) {
    return new YclientsIntegrationError(
      bodyText?.slice(0, 500) ?? 'YCLIENTS invalid payload',
      {
        code: 'invalid_payload',
        httpStatus: status,
        retryable: false,
        correlationId,
      },
    );
  }
  if (status >= 500) {
    return new YclientsIntegrationError('YCLIENTS server error', {
      code: 'provider_unavailable',
      httpStatus: status,
      retryable: true,
      correlationId,
    });
  }
  let code: YclientsErrorCode = 'unknown';
  if (status === 404) {
    code = 'stale_availability';
  }
  return new YclientsIntegrationError(
    bodyText?.slice(0, 500) ?? `YCLIENTS http ${status}`,
    {
      code,
      httpStatus: status,
      retryable: status === 404,
      correlationId,
    },
  );
}
