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
| `VITE_API_BASE_URL` | URL backend API (по умолчанию `http://127.0.0.1:8000`) |

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

## CORS

Backend должен разрешать origin `http://127.0.0.1:5173` (уже настроено в `backend/app/main.py`).
