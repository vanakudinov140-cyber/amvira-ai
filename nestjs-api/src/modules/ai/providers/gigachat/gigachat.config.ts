import type { ConfigService } from '@nestjs/config';

export type ResolvedGigachatConfig = {
  readonly authorizationKey: string;
  readonly oauthUrl: string;
  readonly apiBaseUrl: string;
  readonly scope: string;
  readonly model: string;
  readonly requestTimeoutMs: number;
};

const DEFAULT_OAUTH =
  'https://ngw.devices.sberbank.ru:9443/api/v2/oauth' as const;
const DEFAULT_API_BASE =
  'https://gigachat.devices.sberbank.ru/api/v1' as const;

export function readGigachatConfig(config: ConfigService): ResolvedGigachatConfig {
  const timeoutRaw = config.get<number>('gigachat.requestTimeoutMs', 120_000);
  const timeout =
    typeof timeoutRaw === 'number' && Number.isFinite(timeoutRaw) && timeoutRaw > 0
      ? timeoutRaw
      : 120_000;
  return {
    authorizationKey:
      config.get<string>('gigachat.authorizationKey', '')?.trim() ?? '',
    oauthUrl: firstNonEmpty(
      config.get<string>('gigachat.oauthUrl'),
      DEFAULT_OAUTH,
    ),
    apiBaseUrl: firstNonEmpty(
      config.get<string>('gigachat.apiBaseUrl'),
      DEFAULT_API_BASE,
    ),
    scope: firstNonEmpty(config.get<string>('gigachat.scope'), 'GIGACHAT_API_PERS'),
    model: firstNonEmpty(config.get<string>('gigachat.model'), 'GigaChat'),
    requestTimeoutMs: Math.max(5_000, timeout),
  };
}

function firstNonEmpty(value: string | undefined, fallback: string): string {
  const t = value?.trim();
  return t && t.length > 0 ? t : fallback;
}
