# Деплой Retention CRM на Amvera

Один Docker-образ: **production-сборка React** + **FastAPI** + **nginx** (порт **80**).  
PostgreSQL — **отдельный managed-проект** в Amvera.  
`docker-compose` на Amvera **не поддерживается**.

---

## 1. Что создать в Amvera (2 проекта)

| Проект | Тип | Назначение |
|--------|-----|------------|
| `retention-db` | **PostgreSQL** | База данных (тариф не ниже «Начальный») |
| `retention-crm` | **Приложение** (Docker / Git) | Dashboard + API |

---

## 2. PostgreSQL

1. Главная → **PostgreSQL** → **Создать базу данных**.
2. Задайте имя проекта, тариф, **имя БД**, **пользователя**, **пароль** (не используйте зарезервированные `postgres` как имя БД/пользователя приложения).
3. Дождитесь статуса **PostgreSQL запущен**.
4. На вкладке **Инфо** скопируйте **внутреннее доменное имя** для записи:
   - `amvera-<user>-cnpg-<project>-rw` (чтение/запись)

Соберите `DATABASE_URL`:

```text
postgresql+asyncpg://<user>:<password>@amvera-<user>-cnpg-<pg_project>-rw:5432/<db_name>
```

Пароль с спецсимволами — URL-encode (`@` → `%40` и т.д.).

---

## 3. Приложение (Git deploy)

### 3.1. Репозиторий

В корне репозитория должны быть:

- `Dockerfile` — production-образ
- `amvera.yml` — порт **80**
- `deploy/nginx.conf`, `deploy/docker-entrypoint.sh`
- `.env.amvera.example` — шаблон переменных

**Не коммитьте** `backend/.env` с секретами.

### 3.2. Создание проекта

1. **Приложения** → **Создать проект**.
2. Имя, например: `retention-crm`.
3. Источник: **Git** (GitHub / GitLab / Amvera Git) → выберите репозиторий и ветку (`main`).
4. Amvera обнаружит `amvera.yml` и `Dockerfile` в корне.

### 3.3. Переменные окружения

**Настройки** → **Переменные** / **Секреты**. Минимум:

| Переменная | Обязательно | Пример / описание |
|------------|-------------|-------------------|
| `DATABASE_URL` | да | `postgresql+asyncpg://user:pass@amvera-...-rw:5432/db` |
| `TEST_MODE` | да | `true` |
| `TEST_RECIPIENTS` | да при TEST_MODE | `79991234567,79997654321` |
| `TELEGRAM_BOT_TOKEN` | для Telegram TEST | токен бота |
| `TELEGRAM_TEST_CHAT_ID` | для Telegram TEST | chat id |
| `YCLIENTS_API_KEY` | по необходимости | |
| `YCLIENTS_PARTNER_TOKEN` | по необходимости | |
| `YCLIENTS_COMPANY_ID` | по необходимости | |
| `FLOWSELL_API_URL` | по необходимости | |
| `FLOWSELL_API_KEY` | по необходимости | |
| `LOG_LEVEL` | нет | `INFO` |
| `DEBUG` | нет | `false` |
| `CORS_ORIGINS` | обычно не нужен | `https://<app>.amvera.app` — только если API с другого origin |
| `SCHEDULER_AUTOMATION_ENABLED` | нет | `true` |
| `SEND_PENDING_LIMIT` | нет | `5` |

Полный список — в [.env.amvera.example](../.env.amvera.example).

При старте контейнера выполняется `alembic upgrade head` (миграции).

### 3.4. Сборка и запуск

1. **Сборка** — автоматически после push в Git или кнопка «Собрать».
2. Первая сборка ~5–10 мин (npm + pip).
3. **Запуск** — после успешного образа.

### 3.5. Публичный URL (HTTPS)

1. **Настройки** → **Сеть** / **Домены**.
2. Включите **бесплатное доменное имя Amvera** или привяжите своё.
3. Откройте `https://<ваш-проект>.amvera.app` — dashboard.
4. API на том же origin: `https://<ваш-проект>.amvera.app/health`, `/analytics/...`, `/messages/...`.

Проверка:

```text
GET https://<ваш-проект>.amvera.app/health
→ {"status":"ok","database":"connected"}
```

---

## 4. Архитектура (same-origin)

```text
Браузер → HTTPS (Amvera) → nginx:80
                              ├─ /          → React static (dist)
                              └─ /health, /analytics, /messages, … → uvicorn:127.0.0.1:8000
```

`VITE_API_URL` при сборке пустой — запросы идут на тот же хост (без CORS-проблем).

---

## 5. Порты

| Где | Порт |
|-----|------|
| Контейнер приложения | **80** (`containerPort` в `amvera.yml`) |
| PostgreSQL (внутренний) | **5432** |
| Снаружи | только **443/80** у Amvera (прокси платформы) |

---

## 6. TEST MODE и Telegram

- `TEST_MODE=true` — send-pending **не** шлёт на телефоны клиентов.
- С `TELEGRAM_BOT_TOKEN` + `TELEGRAM_TEST_CHAT_ID` — доставка в тестовый чат.
- В логах приложения: `TELEGRAM TEST SEND SUCCESS` или fallback `TEST SENDER`.

---

## 7. Локальная проверка production-образа

```powershell
cd <корень репозитория>
docker build -t retention-crm:prod .
docker run --rm -p 8080:80 --env-file backend/.env retention-crm:prod
```

Откройте `http://localhost:8080` и `http://localhost:8080/health`.

`DATABASE_URL` должен указывать на доступную с хоста БД.

---

## 8. Чеклист production readiness

- [x] FastAPI + uvicorn, миграции Alembic при старте
- [x] PostgreSQL через `DATABASE_URL` (asyncpg)
- [x] Frontend: `npm run build`, не dev-сервер
- [x] nginx reverse proxy, same-origin API
- [x] Healthcheck `GET /health` (в т.ч. в Dockerfile)
- [x] `TEST_MODE=true` в шаблоне env
- [ ] Заполнить секреты в Amvera
- [ ] Создать PostgreSQL и связать `DATABASE_URL`
- [ ] Push в Git → дождаться сборки → открыть публичный URL

---

## 9. Частые проблемы

| Симптом | Решение |
|---------|---------|
| `503` на `/health`, database disconnected | Проверьте `DATABASE_URL`, доступность `-rw` хоста из проекта приложения |
| Сборка падает на `npm ci` | Закоммитьте `admin-dashboard/package-lock.json` |
| Пустой dashboard | Смотрите логи сборки; проверьте, что `dist` попал в образ |
| CORS в браузере | Убедитесь, что фронт ходит на same-origin (`VITE_API_URL` пустой в Dockerfile) |
| NestJS / старый корневой образ | Используйте актуальный `Dockerfile` из этого репозитория (retention CRM) |

---

## 10. Push для деплоя (кратко)

```bash
git add Dockerfile amvera.yml deploy/ .env.amvera.example .dockerignore
git commit -m "Add Amvera production deployment for retention CRM"
git push origin main
```

В Amvera: проект приложения → привязанный Git → дождаться **Успешная сборка** → **Запущено** → открыть домен.
