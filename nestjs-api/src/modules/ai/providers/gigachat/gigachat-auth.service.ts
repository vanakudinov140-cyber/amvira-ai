import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { randomUUID } from 'node:crypto';
import { readGigachatConfig } from './gigachat.config';
import { GigachatError } from './gigachat.errors';
import type { GigachatOAuthTokenResponse } from './gigachat.types';

const TOKEN_SKEW_MS = 60_000;

@Injectable()
export class GigachatAuthService {
  private readonly logger = new Logger(GigachatAuthService.name);
  private accessToken: string | null = null;
  private expiresAtMs = 0;
  private refreshInFlight: Promise<string> | null = null;

  constructor(private readonly config: ConfigService) {}

  invalidate(): void {
    this.accessToken = null;
    this.expiresAtMs = 0;
  }

  async getAccessToken(): Promise<string> {
    const cfg = readGigachatConfig(this.config);
    if (!cfg.authorizationKey) {
      throw new GigachatError(
        'GIGACHAT_AUTHORIZATION_KEY is empty',
        'auth_failed',
        false,
        undefined,
      );
    }
    if (this.accessToken && Date.now() < this.expiresAtMs - TOKEN_SKEW_MS) {
      return this.accessToken;
    }
    if (!this.refreshInFlight) {
      this.refreshInFlight = this.fetchToken(cfg).finally(() => {
        this.refreshInFlight = null;
      });
    }
    return this.refreshInFlight;
  }

  private async fetchToken(
    cfg: ReturnType<typeof readGigachatConfig>,
  ): Promise<string> {
    const rqUid = randomUUID();
    const body = new URLSearchParams({ scope: cfg.scope }).toString();
    let res: Response;
    try {
      res = await fetch(cfg.oauthUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          Accept: 'application/json',
          RqUID: rqUid,
          Authorization: `Basic ${cfg.authorizationKey}`,
        },
        body,
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      throw new GigachatError(
        `oauth_network: ${msg}`,
        'auth_failed',
        true,
        undefined,
      );
    }

    let json: unknown;
    try {
      json = (await res.json()) as unknown;
    } catch {
      throw new GigachatError(
        'oauth_response_not_json',
        'auth_failed',
        res.status >= 500 || res.status === 429,
        res.status,
      );
    }

    if (!res.ok) {
      const retryable =
        res.status === 429 || res.status >= 500 || res.status === 0;
      throw new GigachatError(
        `oauth_http_${res.status}`,
        'auth_failed',
        retryable,
        res.status,
      );
    }

    const parsed = json as GigachatOAuthTokenResponse;
    const token = parsed.access_token;
    if (!token || typeof token !== 'string') {
      throw new GigachatError(
        'oauth_missing_access_token',
        'auth_failed',
        false,
        res.status,
      );
    }

    const expiresAt =
      typeof parsed.expires_at === 'number' && Number.isFinite(parsed.expires_at)
        ? parsed.expires_at
        : nowMs() + 25 * 60_000;

    this.accessToken = token;
    this.expiresAtMs = expiresAt;

    this.logger.log(
      JSON.stringify({
        msg: 'gigachat.oauth_ok',
        rqUid,
        expiresAtMs: this.expiresAtMs,
      }),
    );

    return token;
  }
}

function nowMs(): number {
  return Date.now();
}
