# Деплой nestjs-api в Amvera

Контейнер из корня `nestjs-api`: `Dockerfile`, точка входа `scripts/docker-entrypoint.sh` (перед стартом выполняется `prisma migrate deploy`).

## 1. `DATABASE_URL` (Prisma / PostgreSQL)

Формат:

```text
postgresql://USER:PASSWORD@HOST:5432/DB_NAME?schema=public
```

- **Внутри Amvera** (приложение и БД в одном облаке): `HOST` = внутреннее имя вида `amvera-<account>-cnpg-<db>-rw`, порт **5432**.
- **Из интернета** (отдельный POSTGRES-домен в настройках сети): в документации Amvera для клиента требуется **SSL** — добавьте к query, например: `?schema=public&sslmode=require` или `sslmode=prefer` (см. [PostgreSQL в Amvera](https://docs.amvera.ru/databases/postgreSQL.html)).

Спецсимволы в `USER` и `PASSWORD` нужно **URL-кодировать** (например `@` → `%40`).

## 2. Переменные в панели Amvera

Скопируйте структуру из `.env.production.example`. На этапе **сборки** образа переменные Amvera **недоступны** — только в рантайме ([переменные и секреты](https://docs.amvera.ru/applications/configuration/variables.html)).

## 3. Миграции Prisma

В образе уже вызывается `prisma migrate deploy` при каждом старте контейнера.

Локально или в one-off job (подставьте свой `DATABASE_URL`):

```bash
cd nestjs-api
set DATABASE_URL=postgresql://...
npx prisma migrate deploy
```

Или npm-скрипт:

```bash
npm run prisma:migrate:deploy
```

Требуется сеть до БД и корректный `DATABASE_URL`.

## 4. Health checks

Префикс `api` для маршрутов **не** применяется к health (см. `main.ts`).

| Проверка | URL | Назначение |
|----------|-----|------------|
| Liveness | `GET /health/live` | Процесс жив, без БД/Redis |
| Readiness | `GET /health/ready` | Postgres + Redis + BullMQ (если `ASYNC_JOBS_USE_BULLMQ=true`) |
| Алиас | `GET /health` | То же, что `/health/ready` |

Для Amvera в качестве readiness обычно указывают **`/health/ready`** или **`/health/live`**, если Redis пока нет (но тогда `/health/ready` вернёт ошибку — лучше поднять Redis).

## 5. Checklist запуска

1. Проект PostgreSQL в статусе «запущен», внутренний **rw**-хост скопирован в `DATABASE_URL`.
2. Проект **Redis** (или совместимый кэш) создан; `REDIS_HOST` / `REDIS_PORT` / `REDIS_PASSWORD` заданы.
3. В приложении API: `NODE_ENV=production`, `PORT` (если платформа не задаёт сама), `TRUST_PROXY=true` за reverse-proxy.
4. `DATABASE_URL` задан **секретом** или переменной в UI.
5. Первый деплой: дождаться логов `[entrypoint] prisma migrate deploy` без ошибки, затем `[entrypoint] starting api`.
6. Проверить `GET /health/live`, затем `GET /health/ready`.
7. Заполнить опциональные переменные под нужные фичи (Telegram, GigaChat, YCLIENTS) — см. раздел ниже.

## 6. Обязательные и опциональные переменные

**Строго обязательные (валидатор `env.validation.ts`):**

- `DATABASE_URL`

**Фактически обязательные для рабочего readiness и очередей:**

- `REDIS_HOST`, `REDIS_PORT` (и `REDIS_PASSWORD`, если у Redis есть пароль)

**Рекомендуемые для продакшена за прокси:**

- `NODE_ENV=production`
- `PORT` — если окружение не выставляет (в коде по умолчанию 3000)
- `TRUST_PROXY=true`

**Опционально (фичи):**

- Telegram: `TELEGRAM_*`
- GigaChat: `GIGACHAT_*`
- YCLIENTS: `YCLIENTS_*`
- `ASYNC_JOBS_USE_BULLMQ=true` только если подняты workers и Redis под BullMQ

Переменная **`AMVERA=1`** задаётся платформой для отличия окружения; приложение её не требует.
