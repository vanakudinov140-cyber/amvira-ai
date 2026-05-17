# Retention Admin Dashboard

Standalone frontend для **AI Retention System** — React SPA + nginx для Amvera.

Backend API (production): `https://retention-v2-ivankudinov.amvera.io`

> Этот репозиторий предназначен для **отдельного** Amvera-проекта.  
> Root path не нужен — `Dockerfile` и `amvera.yml` в корне репозитория.

## Стек

- React 18 + Vite + TypeScript
- Tailwind CSS
- Axios + React Router

## Локальная разработка

```bash
npm install
cp .env.example .env
npm run dev
```

Откройте http://127.0.0.1:5173

## Production build

```bash
npm run build
docker build -t retention-admin:latest .
docker run --rm -p 8080:80 retention-admin:latest
```

## Деплой на Amvera

См. [DEPLOY_AMVERA.md](./DEPLOY_AMVERA.md)

## Переменные (только build-time)

| Переменная | Описание |
|------------|----------|
| `VITE_API_URL` | URL backend API |
| `VITE_ENV_LABEL` | Подпись в шапке UI |

Задаются в `Dockerfile` (`ARG`) или `.env.production` при локальной сборке.
