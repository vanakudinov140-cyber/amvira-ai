# AI Retention Backend

MVP backend для retention-сценария салона красоты: синхронизация с YCLIENTS, отбор кандидатов, шаблоны сообщений, подготовка и отправка через FlowSell (без AI, без очередей и без встроенного scheduler).

## Стек

| Компонент | Технология |
|-----------|------------|
| Runtime | Python 3.12 |
| API | FastAPI, Uvicorn |
| БД | PostgreSQL 16, SQLAlchemy 2.0 (async), asyncpg |
| Миграции | Alembic |
| HTTP-клиенты | httpx |
| Конфиг | pydantic-settings, python-dotenv |
| Контейнеры | Docker, docker-compose |

## Быстрый старт (локально)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
copy .env.example .env          # заполните переменные
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Приложение проверяет при старте, что `DATABASE_URL` (или сборка из `POSTGRES_*`) задан и использует драйвер `postgresql+asyncpg://`.

## Docker Compose

```bash
cd backend
copy .env.example .env
docker compose up --build
```

- API: `http://127.0.0.1:8000`
- PostgreSQL: порт `5432`, данные в volume `postgres_data`
- Сервис `api` подставляет `DATABASE_URL` на хост `db` внутри сети compose

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `APP_NAME` | Название в OpenAPI |
| `DEBUG` | `true` — подробные ошибки в JSON, SQL echo |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, … (корневой логгер) |
| `DATABASE_URL` | Async URL, например `postgresql+asyncpg://user:pass@host:5432/db` |
| `POSTGRES_*` | Альтернатива URL: user, password, db, host, port |
| `YCLIENTS_*` | Интеграция YCLIENTS (опционально для синка) |
| `FLOWSELL_API_URL`, `FLOWSELL_API_KEY` | Отправка сообщений (MVP: `POST {URL}/messages`) |

Полный шаблон — в файле `.env.example`.

## Миграции Alembic

Из каталога `backend` (с активированным venv и доступной БД):

```bash
python -m alembic revision --autogenerate -m "описание"
python -m alembic upgrade head
python -m alembic current
```

На Windows при проблемах asyncpg к Docker-БД удобно запускать Alembic внутри контейнера `api` с примонтированной папкой `alembic/versions`.

## Обзор API (MVP)

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/health` | Статус API и PostgreSQL |
| POST | `/sync/clients`, `/sync/procedures`, `/sync/visits` | Синхронизация из YCLIENTS |
| GET | `/retention/candidates` | Кандидаты retention |
| POST | `/retention/preview-message` | Превью текста сообщения |
| POST | `/messages/prepare-retention` | Запись подготовленных сообщений |
| GET | `/messages/pending` | Ожидающие отправки |
| POST | `/messages/send-pending` | Отправка через FlowSell |
| GET | `/messages/stats` | Счётчики по статусам |

Документация интерактивно: `/docs`, `/redoc`.

## Логирование и ошибки

- Единый формат логов: время, уровень, имя логгера, сообщение (`app/core/logging.py`).
- Ошибки API в едином виде: `{"success": false, "error": "..."}` (глобальные handlers в `app/core/exception_handlers.py`).

## Структура репозитория (backend)

```
backend/
├── app/
│   ├── api/routes/
│   ├── core/           # config, logging, exception_handlers
│   ├── db/
│   ├── integrations/ # yclients, flowsell
│   ├── models/
│   └── services/
├── alembic/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Лицензия / продукт

Внутренний MVP; детали лицензии задайте отдельно при выкладке в open source.
