# Retention Admin Dashboard

Внутренняя admin panel для AI Retention System (модерация, аналитика, ручная отправка).

## Стек

- React 18 + Vite + TypeScript
- Tailwind CSS
- shadcn/ui-style components
- Axios

## Требования

- Node.js 18+
- Запущенный FastAPI backend: `http://127.0.0.1:8000`

## Установка и запуск

```bash
cd admin-dashboard
npm install
cp .env.example .env
npm run dev
```

Откройте: [http://127.0.0.1:5173](http://127.0.0.1:5173)

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `VITE_API_URL` | URL backend API (production: `https://retention-v2-ivankudinov.amvera.io`) |
| `VITE_ENV_LABEL` | Подпись окружения в шапке |

## Возможности UI

1. **Analytics** — карточки из `/analytics/retention-overview`, статус scheduler
2. **Moderation Queue** — таблица pending, Approve / Reject / Edit
3. **Message Editor** — `PATCH /messages/{id}` перед approve
4. **Manual Send** — `POST /messages/send-pending` (только approved)

Автообновление данных каждые **30 секунд**.

## Сборка production

```bash
npm run build
npm run preview
```

## Деплой на Amvera

См. [DEPLOY_AMVERA.md](./DEPLOY_AMVERA.md).

Ожидаемый URL после деплоя: **https://retention-admin-ivankudinov.amvera.app**

## CORS

Backend разрешает `*.amvera.io` и `*.amvera.app` (regex в `backend/app/main.py`) и локальные порты Vite.
