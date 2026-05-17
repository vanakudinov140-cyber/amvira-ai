# Деплой Retention CRM на Amvera

Один Docker-образ: **FastAPI (uvicorn)** на порту **8000**.  
PostgreSQL — **отдельный managed-проект** в Amvera.  
`docker-compose` на Amvera **не поддерживается**.

---

## 1. Что создать в Amvera (2 проекта)

| Проект | Тип | Назначение |
|--------|-----|------------|
| `retention-db` | **PostgreSQL** | База данных (тариф не ниже «Начальный») |
| `retention-crm` | **Приложение** (Docker / Git) | API (uvicorn) |

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

- `Dockerfile` — production-образ (uvicorn)
- `amvera.yml` — порт **8000**
- `deploy/docker-entrypoint.sh`
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
| `CORS_ORIGINS` | при отдельном фронте | `https://<frontend-host>` |
| `SCHEDULER_AUTOMATION_ENABLED` | нет | `true` |
| `SEND_PENDING_LIMIT` | нет | `5` |

Полный список — в [.env.amvera.example](../.env.amvera.example).

При старте контейнера выполняется `alembic upgrade head` (миграции).

### 3.4. Сборка и запуск

1. **Сборка** — автоматически после push в Git или кнопка «Собрать».
2. Первая сборка ~3–5 мин (pip).
3. **Запуск** — после успешного образа.

**Не задавайте** `run.command` в UI Amvera — используется `ENTRYPOINT` из Dockerfile.

### 3.5. Публичный URL (HTTPS)

1. **Настройки** → **Сеть** / **Домены**.
2. Включите **бесплатное доменное имя Amvera** или привяжите своё.
3. API: `https://<ваш-проект>.amvera.app/health`, `/analytics/...`, `/messages/...`, `/docs`.

Проверка:

```text
GET https://<ваш-проект>.amvera.app/health
→ {"status":"ok","database":"connected"}
```

---

## 4. Архитектура

```text
Браузер / клиент → HTTPS (Amvera) → uvicorn:0.0.0.0:8000
```

Admin-dashboard для production разворачивается отдельно (см. `docker-compose.demo.yml`) или локально через `npm run dev`.

---

## 5. Порты

| Где | Порт |
|-----|------|
| Контейнер приложения | **8000** (`containerPort` в `amvera.yml`) |
| PostgreSQL (внутренний) | **5432** |
| Снаружи | HTTPS у Amvera (прокси платформы → 8000) |

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
docker run --rm -p 8080:8000 --env-file backend/.env retention-crm:prod
```

Откройте `http://localhost:8080/health`.

`DATABASE_URL` должен указывать на доступную с хоста БД.

---

## 8. Чеклист production readiness

- [x] FastAPI + uvicorn, миграции Alembic при старте
- [x] PostgreSQL через `DATABASE_URL` (asyncpg)
- [x] Healthcheck `GET /health` на `:8000`
- [x] `TEST_MODE=true` в шаблоне env
- [ ] Заполнить секреты в Amvera
- [ ] Создать PostgreSQL и связать `DATABASE_URL`
- [ ] Push в Git → дождаться сборки → открыть публичный URL

---

## 9. Частые проблемы

| Симптом | Решение |
|---------|---------|
| `503` на `/health`, database disconnected | Проверьте `DATABASE_URL`, доступность `-rw` хоста из проекта приложения |
| `502` / connection refused | Убедитесь, что `containerPort` и `servicePort` = **8000**, нет `run.command` в UI |
| NestJS / старый корневой образ | Используйте актуальный `Dockerfile` из этого репозитория (retention CRM) |

---

## 10. Push для деплоя (кратко)

```bash
git add Dockerfile amvera.yml deploy/ .env.amvera.example docker-compose.prod.yml
git commit -m "Remove nginx from production deploy, uvicorn only on port 8000"
git push origin main
```

В Amvera: проект приложения → привязанный Git → дождаться **Успешная сборка** → **Запущено** → открыть домен.
