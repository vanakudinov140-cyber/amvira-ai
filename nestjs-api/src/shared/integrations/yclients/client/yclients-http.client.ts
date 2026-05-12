import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { classifyYclientsHttpFailure } from '../errors/yclients-error.mapper';
import { YclientsIntegrationError } from '../errors/yclients-integration.error';
import type {
  YclientsHttpResponse,
  YclientsJsonRequest,
} from '../contracts/yclients-http.contract';
import { YCLIENTS_HTTP_HEADERS } from '../contracts/yclients-http.contract';

const sleep = (ms: number) =>
  new Promise<void>((resolve) => {
    setTimeout(resolve, ms);
  });

@Injectable()
export class YclientsHttpClient {
  private readonly logger = new Logger(YclientsHttpClient.name);

  constructor(private readonly config: ConfigService) {}

  async requestJson<T = unknown>(
    req: YclientsJsonRequest,
  ): Promise<YclientsHttpResponse<T>> {
    const baseUrl = this.config.get<string>('yclients.apiBaseUrl') ?? '';
    const partnerToken = this.config.get<string>('yclients.partnerToken') ?? '';
    const userToken = this.config.get<string>('yclients.userToken') ?? '';
    const timeoutMs = this.config.get<number>('yclients.requestTimeoutMs') ?? 15000;

    if (!baseUrl || !partnerToken || !userToken) {
      throw new YclientsIntegrationError('YCLIENTS not configured', {
        code: 'provider_unavailable',
        retryable: false,
        correlationId: req.correlationId,
      });
    }

    const url = new URL(req.path.replace(/^\//, ''), baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`);
    if (req.query) {
      for (const [k, v] of Object.entries(req.query)) {
        if (v !== undefined) {
          url.searchParams.set(k, String(v));
        }
      }
    }

    const headers: Record<string, string> = {
      Accept: YCLIENTS_HTTP_HEADERS.accept,
      'Content-Type': YCLIENTS_HTTP_HEADERS.contentType,
      Authorization: `Bearer ${partnerToken}, User ${userToken}`,
    };
    if (req.correlationId) {
      headers['X-Correlation-Id'] = req.correlationId;
    }

    const maxAttempts = 4;
    let attempt = 0;
    let lastErr: unknown;
    let totalMs = 0;
    let retryCount = 0;

    while (attempt < maxAttempts) {
      attempt += 1;
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      const started = Date.now();
      try {
        const res = await fetch(url.toString(), {
          method: req.method,
          headers,
          body:
            req.method === 'GET' || req.body === undefined
              ? undefined
              : JSON.stringify(req.body),
          signal: controller.signal,
        });
        const text = await res.text();
        let data: unknown = text;
        try {
          data = text ? JSON.parse(text) : null;
        } catch {
          data = text;
        }
        const attemptMs = Date.now() - started;
        totalMs += attemptMs;

        if (!res.ok) {
          const mapped = classifyYclientsHttpFailure({
            status: res.status,
            bodyText: typeof text === 'string' ? text : undefined,
            correlationId: req.correlationId,
          });
          if (mapped.retryable && attempt < maxAttempts) {
            retryCount += 1;
            const backoff = Math.min(2000, 200 * 2 ** (attempt - 1));
            this.logger.warn({
              msg: 'yclients_http_retry',
              status: res.status,
              attempt,
              backoffMs: backoff,
              correlationId: req.correlationId,
              path: req.path,
            });
            await sleep(backoff);
            continue;
          }
          throw mapped;
        }

        return {
          ok: true,
          status: res.status,
          data: data as T,
          requestMs: totalMs,
          retryCount,
        };
      } catch (e) {
        const attemptMs = Date.now() - started;
        totalMs += attemptMs;
        lastErr = e;
        if (e instanceof YclientsIntegrationError && !e.retryable) {
          throw e;
        }
        const isAbort =
          e instanceof Error &&
          (e.name === 'AbortError' || e.message.includes('aborted'));
        if (attempt < maxAttempts && (isAbort || !(e instanceof YclientsIntegrationError))) {
          retryCount += 1;
          const backoff = Math.min(2000, 200 * 2 ** (attempt - 1));
          this.logger.warn({
            msg: 'yclients_http_retry_network',
            attempt,
            backoffMs: backoff,
            correlationId: req.correlationId,
            path: req.path,
            error: e instanceof Error ? e.message : String(e),
          });
          await sleep(backoff);
          continue;
        }
        if (isAbort) {
          throw new YclientsIntegrationError('YCLIENTS request timeout', {
            code: 'provider_unavailable',
            retryable: true,
            correlationId: req.correlationId,
          });
        }
        throw e;
      } finally {
        clearTimeout(timer);
      }
    }

    this.logger.error({
      msg: 'yclients_http_exhausted',
      correlationId: req.correlationId,
      path: req.path,
      error: lastErr instanceof Error ? lastErr.message : String(lastErr),
    });
    throw lastErr instanceof Error
      ? lastErr
      : new YclientsIntegrationError('YCLIENTS request failed', {
          code: 'provider_unavailable',
          retryable: false,
          correlationId: req.correlationId,
        });
  }
}
