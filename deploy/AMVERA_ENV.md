# Переменные окружения — Backend (Amvera)

Проект: **retention API** (корень репозитория, `Dockerfile`, `amvera.yml`).  
PostgreSQL — **отдельный managed-проект** в Amvera.

---

## Обязательные

| Переменная | Описание | Пример |
|------------|----------|--------|
| `DATABASE_URL` | Async SQLAlchemy URL (**asyncpg**). Внутренний хост из карточки PostgreSQL (`…-rw`) | `postgresql+asyncpg://app_user:SECRET@amvera-ivankudinov-cnpg-retention-db-rw:5432/retention` |
| `ENVIRONMENT` | Режим приложения; на Amvera всегда `production` | `production` |
| `TEST_MODE` | Безопасная отправка (не на телефоны клиентов) | `true` |
| `TEST_RECIPIENTS` | Номера для TEST_MODE (через запятую) | `79991234567` |

При `TEST_MODE=true` без `TEST_RECIPIENTS` приложение **не стартует** (валидация Pydantic).

---

## Рекомендуемые для production-test

| Переменная | Описание | Пример |
|------------|----------|--------|
| `TELEGRAM_BOT_TOKEN` | Бот для доставки в тестовый чат | `123456:ABC…` |
| `TELEGRAM_TEST_CHAT_ID` | Chat ID модератора | `-1001234567890` |
| `LOG_LEVEL` | Уровень логов | `INFO` |
| `DEBUG` | Режим отладки FastAPI | `false` |

---

## YCLIENTS (для синхронизации клиентов/визитов)

| Переменная | Обязательно | Описание |
|------------|-------------|----------|
| `YCLIENTS_API_KEY` | для sync | User token |
| `YCLIENTS_PARTNER_TOKEN` | для sync | Partner Bearer |
| `YCLIENTS_COMPANY_ID` | для sync | ID компании |
| `YCLIENTS_BASE_URL` | нет | По умолчанию `https://api.yclients.com/api/v1` |

---

## FlowSell WhatsApp (реальная отправка, когда TEST_MODE=false)

| Переменная | Обязательно | Описание |
|------------|-------------|----------|
| `FLOWSELL_API_BASE_URL` | нет | `https://dev.flowsell.me/api/v1` |
| `FLOWSELL_INSTANCE_ID` | при prod send | idInstance из кабинета |
| `FLOWSELL_API_KEY` | при prod send | apiTokenInstance |

См. [FLOWSELL_INTEGRATION.md](./FLOWSELL_INTEGRATION.md)

---

## Retention / scheduler (optional, есть defaults)

| Переменная | Default | Описание |
|------------|---------|----------|
| `SCHEDULER_AUTOMATION_ENABLED` | `true` | Фоновый scheduler |
| `SEND_PENDING_LIMIT` | `5` | Batch send-pending |
| `RETENTION_ATTRIBUTION_DAYS` | `30` | Окно атрибуции возврата |
| `DUPLICATE_WINDOW_DAYS` | `7` | Антидубликат сообщений |
| `RETENTION_COOLDOWN_DAYS` | `14` | Кулдаун между кампаниями |
| `DAILY_SEND_LIMIT` | `50` | Лимит отправок в сутки |
| `QUIET_HOURS_START` | `21` | Начало тихих часов (UTC) |
| `QUIET_HOURS_END` | `10` | Конец тихих часов (UTC) |

---

## AI (optional)

| Переменная | Default | Описание |
|------------|---------|----------|
| `AI_REWRITE_ENABLED` | `false` | Переписывание текстов |
| `AI_PROVIDER` | `mock` | `mock` / будущие провайдеры |

---

## CORS / proxy (optional)

| Переменная | Default | Описание |
|------------|---------|----------|
| `CORS_ORIGINS` | — | Доп. origins через запятую |
| `ROOT_PATH` | — | Префикс за reverse proxy (обычно пусто на Amvera) |

Regex `https://.*\.amvera\.(io|app)` уже включён в код.

---

## Не задавать на Amvera (fallback → localhost)

| Переменная | Почему |
|------------|--------|
| `POSTGRES_HOST` | Default `localhost` — **источник ошибки** |
| `POSTGRES_PORT` | Используйте только `DATABASE_URL` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | То же |

---

## Как собрать DATABASE_URL

1. Amvera → **PostgreSQL** → ваш проект → **Инфо**.
2. Скопируйте **внутреннее доменное имя** (read-write):  
   `amvera-<account>-cnpg-<pg_project>-rw`
3. Формат:

```text
postgresql+asyncpg://<db_user>:<url_encoded_password>@amvera-<account>-cnpg-<pg_project>-rw:5432/<db_name>
```

Пароль со спецсимволами — URL-encode (`@` → `%40`, `#` → `%23`).

---

## Проверка после деплоя

```text
GET https://<api-project>.amvera.io/health
→ {"status":"ok"}

GET https://<api-project>.amvera.io/health/db
→ {"status":"ok","database":"connected"}
```

В логах контейнера при старте:

```text
[entrypoint] DATABASE_URL host: amvera-...-cnpg-...-rw
[entrypoint] ENVIRONMENT: production
Окружение: production, database host: amvera-...-rw
```

---

## Frontend — отдельный GitHub-репозиторий

| Вопрос | Ответ |
|--------|--------|
| Репозиторий | **`retention-admin-frontend`** (standalone, не monorepo) |
| Root path в Amvera | **пусто** (корень repo) |
| Runtime env | не нужны |
| API URL | `VITE_API_URL` в корневом `Dockerfile` |

Экспорт из monorepo: `retention-admin-frontend/`.  
Деплой: `retention-admin-frontend/DEPLOY_AMVERA.md`  
Публикация: `scripts/publish-retention-admin-frontend.ps1`

---

## Шаблон для копирования в Amvera UI

```env
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@amvera-USER-cnpg-DBPROJECT-rw:5432/DBNAME

TEST_MODE=true
TEST_RECIPIENTS=79990000000

LOG_LEVEL=INFO
DEBUG=false

TELEGRAM_BOT_TOKEN=
TELEGRAM_TEST_CHAT_ID=

YCLIENTS_API_KEY=
YCLIENTS_PARTNER_TOKEN=
YCLIENTS_COMPANY_ID=0

FLOWSELL_API_URL=
FLOWSELL_API_KEY=

SCHEDULER_AUTOMATION_ENABLED=true
SEND_PENDING_LIMIT=5
CORS_ORIGINS=https://retention-admin-ivankudinov.amvera.app
```
