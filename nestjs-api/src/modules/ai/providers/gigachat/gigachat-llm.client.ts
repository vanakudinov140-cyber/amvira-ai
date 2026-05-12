import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { randomUUID } from 'node:crypto';
import type { LlmClient } from '../../contracts/llm.client';
import type { LlmInvocationRequest, LlmInvocationResponse } from '../../contracts/llm.invocation';
import { GigachatAuthService } from './gigachat-auth.service';
import { readGigachatConfig } from './gigachat.config';
import { GigachatError, isRetryableGigachatError } from './gigachat.errors';
import { mapGigachatChatCompletionToLlmResponse } from './gigachat-response.mapper';

const MAX_CHAT_ATTEMPTS = 3;
const RETRY_BASE_DELAY_MS = 400;

@Injectable()
export class GigachatLlmClient implements LlmClient {
  private readonly logger = new Logger(GigachatLlmClient.name);

  constructor(
    private readonly config: ConfigService,
    private readonly auth: GigachatAuthService,
  ) {}

  async generate(request: LlmInvocationRequest): Promise<LlmInvocationResponse> {
    const cfg = readGigachatConfig(this.config);
    const rqUid = resolveRqUid(request.correlationId);
    let didInvalidate401 = false;

    for (let attempt = 1; attempt <= MAX_CHAT_ATTEMPTS; attempt++) {
      try {
        const token = await this.auth.getAccessToken();
        const url = `${trimTrailingSlash(cfg.apiBaseUrl)}/chat/completions`;
        const res = await this.fetchWithTimeout(
          url,
          {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json',
              Accept: 'application/json',
              RqUID: rqUid,
            },
            body: JSON.stringify({
              model: cfg.model,
              messages: request.messages.map((m) => ({
                role: m.role,
                content: m.content,
              })),
              temperature: request.temperature ?? 0.2,
              max_tokens: request.maxTokens ?? 1024,
            }),
          },
          cfg.requestTimeoutMs,
        );

        if (res.status === 401 && !didInvalidate401) {
          this.auth.invalidate();
          didInvalidate401 = true;
          continue;
        }

        const text = await res.text();
        let json: unknown;
        try {
          json = text ? (JSON.parse(text) as unknown) : null;
        } catch {
          throw new GigachatError(
            'chat_response_invalid_json',
            'malformed_response',
            false,
            res.status,
          );
        }

        if (!res.ok) {
          throw httpStatusToGigachatError(res.status, json);
        }

        const parsed = mapGigachatChatCompletionToLlmResponse(json);

        this.logger.log(
          JSON.stringify({
            msg: 'gigachat.chat_ok',
            correlationId: request.correlationId ?? null,
            rqUid,
            attempt,
            finishReason: parsed.llm.finishReason ?? null,
            usage: parsed.usageLog ?? null,
          }),
        );

        return parsed.llm;
      } catch (e) {
        const retryable = isRetryableFailure(e);
        const is401 =
          e instanceof GigachatError &&
          e.httpStatus === 401 &&
          e.kind === 'http_error';

        if (is401 && !didInvalidate401) {
          this.auth.invalidate();
          didInvalidate401 = true;
          continue;
        }

        this.logger.warn(
          JSON.stringify({
            msg: 'gigachat.chat_error',
            correlationId: request.correlationId ?? null,
            rqUid,
            attempt,
            error:
              e instanceof GigachatError
                ? { kind: e.kind, httpStatus: e.httpStatus, retryable: e.retryable }
                : { kind: 'unknown', message: String(e) },
          }),
        );

        if (retryable && attempt < MAX_CHAT_ATTEMPTS) {
          await sleep(RETRY_BASE_DELAY_MS * attempt);
          continue;
        }

        throw e;
      }
    }

    throw new GigachatError(
      'gigachat_exhausted_retries',
      'provider_error',
      false,
      undefined,
    );
  }

  private async fetchWithTimeout(
    url: string,
    init: RequestInit,
    timeoutMs: number,
  ): Promise<Response> {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), timeoutMs);
    try {
      return await fetch(url, { ...init, signal: ac.signal });
    } catch (e) {
      if (isAbortError(e)) {
        throw new GigachatError(
          `request_timeout_${timeoutMs}ms`,
          'timeout',
          true,
          undefined,
        );
      }
      const msg = e instanceof Error ? e.message : String(e);
      throw new GigachatError(
        `fetch_failed: ${msg}`,
        'http_error',
        true,
        undefined,
      );
    } finally {
      clearTimeout(timer);
    }
  }
}

function trimTrailingSlash(s: string): string {
  return s.replace(/\/+$/, '');
}

function resolveRqUid(correlationId?: string): string {
  if (correlationId && isUuid(correlationId)) {
    return correlationId;
  }
  return randomUUID();
}

function isUuid(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
    value,
  );
}

function httpStatusToGigachatError(status: number, body: unknown): GigachatError {
  const retryable = status === 429 || status >= 500;
  const code = extractProviderCode(body);
  return new GigachatError(
    `chat_http_${status}`,
    'http_error',
    retryable,
    status,
    code,
  );
}

function extractProviderCode(body: unknown): number | undefined {
  if (!body || typeof body !== 'object') {
    return undefined;
  }
  const err = (body as { error?: { code?: number } }).error;
  return typeof err?.code === 'number' ? err.code : undefined;
}

function isRetryableFailure(err: unknown): boolean {
  if (isRetryableGigachatError(err)) {
    return true;
  }
  if (!(err instanceof GigachatError)) {
    return false;
  }
  if (err.kind === 'timeout') {
    return true;
  }
  if (err.kind === 'http_error' && err.retryable) {
    return true;
  }
  if (err.kind === 'provider_error' && err.retryable) {
    return true;
  }
  return false;
}

function isAbortError(e: unknown): boolean {
  if (!e || typeof e !== 'object') {
    return false;
  }
  const name = (e as { name?: string }).name;
  const code = (e as { code?: string }).code;
  return name === 'AbortError' || code === 'ABORT_ERR';
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}
