# Beauty salon assistant — NestJS API

## Runtime (local)

1. Copy environment: `cp .env.example .env` and fill secrets (`DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `GIGACHAT_*`, …).
2. Start Postgres and Redis (or use Docker Compose infra only — see below).
3. `npm ci`
4. `npx prisma migrate deploy`
5. `npx prisma generate` (also runs on `npm install` via `postinstall`)
6. `npm run start:dev`

- HTTP API base path: **`/api`** (e.g. `POST /api/channels/telegram/webhook`).
- Health (no `/api` prefix): **`GET /health/live`**, **`GET /health/ready`**, `GET /health` (alias of ready).
- Swagger UI: **`GET /docs`** (excluded from global prefix).

## Runtime (Docker Compose)

From this directory (`nestjs-api/`):

```bash
cp .env.example .env
# Ensure TELEGRAM_* / GIGACHAT_* etc. in .env; compose overrides DATABASE_URL + REDIS_* for services.
docker compose up --build
```

- API: `http://localhost:3000`
- Postgres: `localhost:5432` (user/password/db `salon` / `salon` / `salon` — see `docker-compose.yml`)
- Entrypoint runs **`prisma migrate deploy`** then **`node dist/main.js`**.

## Telegram

1. Create a bot with [@BotFather](https://t.me/BotFather), set `TELEGRAM_BOT_TOKEN`.
2. Optional: `TELEGRAM_WEBHOOK_SECRET_TOKEN` — must match header `x-telegram-bot-api-secret-token` on incoming requests.
3. Set `TELEGRAM_MVP_DEFAULT_DIALOG_ID` to an existing dialog UUID for the MVP mapper.
4. Webhook URL must hit **`https://<public-host>/api/channels/telegram/webhook`** (HTTPS required by Telegram in production).

### Webhook setup

- **Manual:** call Telegram `setWebhook` with the same URL and optional `secret_token`.
- **On startup:** set `TELEGRAM_WEBHOOK_SYNC_ON_STARTUP=true` and `TELEGRAM_WEBHOOK_URL=https://…/api/channels/telegram/webhook`; the app calls Telegram on boot (`TelegramWebhookBootstrapService`).

### Local tunnel (example)

Expose local port 3000:

```bash
# e.g. cloudflared (https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/)
cloudflared tunnel --url http://localhost:3000
```

Use the printed HTTPS URL + `/api/channels/telegram/webhook` as `TELEGRAM_WEBHOOK_URL`.

## Production notes

- Run behind a reverse proxy; set `TRUST_PROXY=true` (or `1` / `yes`) so Express respects `X-Forwarded-*`.
- Tune `REQUEST_BODY_LIMIT` (default `512kb`) for your largest JSON payloads.
- Use real secrets for Postgres/Redis; restrict network access.
- For BullMQ async delivery set `ASYNC_JOBS_USE_BULLMQ=true` and ensure Redis is reachable — readiness checks include BullMQ when enabled.
- Prefer managed Postgres/Redis in production; keep `restart: unless-stopped` in Compose for single-node demos only.

## E2E smoke (Telegram → AI)

With DB migrated, dialog id configured, GigaChat and Telegram tokens set, and webhook pointed at `/api/channels/telegram/webhook`, a text message to the bot should return JSON `{ ok: true, status: … }` from the webhook handler after `ConversationOrchestratorService` runs.
