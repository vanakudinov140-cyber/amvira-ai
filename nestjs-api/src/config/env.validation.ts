import * as Joi from 'joi';

export const validationSchema = Joi.object({
  NODE_ENV: Joi.string()
    .valid('development', 'production', 'test')
    .default('development'),
  PORT: Joi.number().port().default(3000),
  DATABASE_URL: Joi.string().required(),
  REDIS_HOST: Joi.string().default('localhost'),
  REDIS_PORT: Joi.number().port().default(6379),
  REDIS_PASSWORD: Joi.string().allow('', null).optional(),
  TELEGRAM_BOT_TOKEN: Joi.string().allow('').optional(),
  TELEGRAM_WEBHOOK_SECRET_TOKEN: Joi.string().allow('').optional(),
  TELEGRAM_MVP_DEFAULT_DIALOG_ID: Joi.string().allow('').optional(),
  TELEGRAM_WEBHOOK_URL: Joi.string().max(2048).allow('').optional(),
  TELEGRAM_WEBHOOK_SYNC_ON_STARTUP: Joi.boolean().default(false),
  GIGACHAT_AUTHORIZATION_KEY: Joi.string().allow('').optional(),
  GIGACHAT_OAUTH_URL: Joi.string().uri().allow('').optional(),
  GIGACHAT_API_BASE_URL: Joi.string().uri().allow('').optional(),
  GIGACHAT_SCOPE: Joi.string().allow('').optional(),
  GIGACHAT_MODEL: Joi.string().allow('').optional(),
  GIGACHAT_REQUEST_TIMEOUT_MS: Joi.number().integer().min(1000).optional(),
  ASYNC_JOBS_USE_BULLMQ: Joi.boolean().default(false),
  SALON_DISPLAY_NAME: Joi.string().allow('').optional(),
  TRUST_PROXY: Joi.boolean().default(false),
  REQUEST_BODY_LIMIT: Joi.string().default('512kb'),
  YCLIENTS_API_BASE_URL: Joi.string().max(512).allow('').optional(),
  YCLIENTS_PARTNER_TOKEN: Joi.string().allow('').optional(),
  YCLIENTS_COMPANY_ID: Joi.string().allow('').optional(),
  YCLIENTS_USER_TOKEN: Joi.string().allow('').optional(),
  YCLIENTS_REQUEST_TIMEOUT_MS: Joi.number().integer().min(1000).max(120000).optional(),
  YCLIENTS_ENABLE_SYNC: Joi.boolean().default(false),
  YCLIENTS_CACHE_TTL_SECONDS: Joi.number().integer().min(30).max(86400).optional(),
});
