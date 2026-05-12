export const YCLIENTS_HTTP_HEADERS = {
  accept: 'application/vnd.yclients.v2+json',
  contentType: 'application/json',
} as const;

export type YclientsHttpMethod = 'GET' | 'POST' | 'DELETE';

export type YclientsJsonRequest = {
  readonly method: YclientsHttpMethod;
  /** Path relative to API base (no leading slash). */
  readonly path: string;
  readonly query?: Readonly<Record<string, string | number | boolean | undefined>>;
  readonly body?: unknown;
  readonly correlationId?: string;
};

export type YclientsHttpResponse<T> = {
  readonly ok: boolean;
  readonly status: number;
  readonly data: T;
  readonly requestMs: number;
  readonly retryCount: number;
};
