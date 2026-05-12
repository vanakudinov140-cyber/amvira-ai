export default () => ({
  app: {
    port: parseInt(process.env.PORT ?? '3000', 10),
    nodeEnv: process.env.NODE_ENV ?? 'development',
  },
  database: {
    url: process.env.DATABASE_URL ?? '',
  },
  redis: {
    host: process.env.REDIS_HOST ?? 'localhost',
    port: parseInt(process.env.REDIS_PORT ?? '6379', 10),
    password: process.env.REDIS_PASSWORD ?? '',
  },
  telegram: {
    botToken: process.env.TELEGRAM_BOT_TOKEN ?? '',
    webhookSecretToken: process.env.TELEGRAM_WEBHOOK_SECRET_TOKEN ?? '',
    mvpDefaultDialogId: process.env.TELEGRAM_MVP_DEFAULT_DIALOG_ID ?? '',
    webhookUrl: process.env.TELEGRAM_WEBHOOK_URL ?? '',
    webhookSyncOnStartup:
      process.env.TELEGRAM_WEBHOOK_SYNC_ON_STARTUP === 'true',
  },
  gigachat: {
    authorizationKey: process.env.GIGACHAT_AUTHORIZATION_KEY ?? '',
    oauthUrl: process.env.GIGACHAT_OAUTH_URL ?? '',
    apiBaseUrl: process.env.GIGACHAT_API_BASE_URL ?? '',
    scope: process.env.GIGACHAT_SCOPE ?? '',
    model: process.env.GIGACHAT_MODEL ?? '',
    requestTimeoutMs: process.env.GIGACHAT_REQUEST_TIMEOUT_MS
      ? parseInt(process.env.GIGACHAT_REQUEST_TIMEOUT_MS, 10)
      : 0,
  },
  asyncJobs: {
    useBullmq: process.env.ASYNC_JOBS_USE_BULLMQ === 'true',
  },
  salon: {
    displayName: process.env.SALON_DISPLAY_NAME ?? '',
  },
  server: {
    trustProxy:
      process.env.TRUST_PROXY === 'true' ||
      process.env.TRUST_PROXY === '1' ||
      process.env.TRUST_PROXY === 'yes',
    requestBodyLimit: process.env.REQUEST_BODY_LIMIT ?? '512kb',
  },
  yclients: {
    apiBaseUrl:
      process.env.YCLIENTS_API_BASE_URL ?? 'https://api.yclients.com/api/v1',
    partnerToken: process.env.YCLIENTS_PARTNER_TOKEN ?? '',
    companyId: process.env.YCLIENTS_COMPANY_ID ?? '',
    userToken: process.env.YCLIENTS_USER_TOKEN ?? '',
    requestTimeoutMs: process.env.YCLIENTS_REQUEST_TIMEOUT_MS
      ? parseInt(process.env.YCLIENTS_REQUEST_TIMEOUT_MS, 10)
      : 15000,
    enableSync: process.env.YCLIENTS_ENABLE_SYNC === 'true',
    cacheTtlSeconds: process.env.YCLIENTS_CACHE_TTL_SECONDS
      ? parseInt(process.env.YCLIENTS_CACHE_TTL_SECONDS, 10)
      : 300,
  },
});
