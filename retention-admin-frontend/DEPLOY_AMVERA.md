# Деплой на Amvera (standalone frontend repo)

Репозиторий содержит **только** admin-dashboard. Amvera собирает корневой `Dockerfile` (nginx + SPA).

Backend API: `https://retention-v2-ivankudinov.amvera.io`

---

## 1. Создать GitHub-репозиторий

1. GitHub → **New repository** → `retention-admin-frontend` (private/public).
2. Запушить содержимое **этой папки** в корень репозитория (не monorepo).

```bash
cd retention-admin-frontend
git init
git add .
git commit -m "init: retention admin dashboard standalone"
git branch -M main
git remote add origin https://github.com/<user>/retention-admin-frontend.git
git push -u origin main
```

---

## 2. Создать проект в Amvera

1. **Приложения** → **Создать** → **Docker / Git**.
2. Имя: `retention-admin-ivankudinov` (или своё).
3. Репозиторий: **`retention-admin-frontend`** (отдельный от backend).
4. Ветка: `main`.
5. **Root path / подпапка:** оставить **пустым** (корень репозитория).
6. Amvera найдёт `amvera.yml` + `Dockerfile` в корне.

---

## 3. Порты

| Параметр | Значение |
|----------|----------|
| `containerPort` | 80 |
| `servicePort` | 80 |

Runtime env в UI **не нужны**.

---

## 4. Проверка сборки (логи Docker)

Должно быть:

- `node:22-alpine`, `npm ci`, `npm run build`
- `nginx:1.27-alpine`, `COPY nginx.conf`
- `EXPOSE 80`

**Не должно быть:** `uvicorn`, `fastapi`, `COPY backend/app`, `EXPOSE 8000`.

---

## 5. Проверка после деплоя

| URL | Ожидание |
|-----|----------|
| `/` | Dashboard, API badge online |
| `/candidates` | Список кандидатов |
| `/pending` | Сообщения на модерации |
| `/sync` | Кнопки синхронизации |
| F5 на любом маршруте | 200, не 404 |

Публичный URL: **https://retention-admin-ivankudinov.amvera.app**

---

## 6. CORS

Backend (`retention-v2-ivankudinov.amvera.io`) разрешает `https://.*\.amvera\.(io|app)`.

При необходимости добавьте в backend `CORS_ORIGINS` точный URL фронта.

---

## 7. Troubleshooting

| Симптом | Решение |
|---------|---------|
| Собирается backend (uvicorn, 8000) | Подключён **не тот** репозиторий или monorepo без root path |
| 503 | Дождаться сборки; смотреть логи nginx |
| API offline | Проверить `https://retention-v2-ivankudinov.amvera.io/health` |
| Сменить API URL | Изменить `ARG VITE_API_URL` в `Dockerfile`, пересобрать |
