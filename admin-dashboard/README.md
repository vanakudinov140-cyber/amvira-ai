# ⚠️ Deprecated — use standalone repo

Admin dashboard перенесён в отдельный репозиторий для Amvera:

**`retention-admin-frontend/`** в этом monorepo — готовый экспорт для push в отдельный GitHub repo.

## Почему

Amvera в monorepo **не применяет** root path `admin-dashboard/` и собирает корневой backend `Dockerfile` (uvicorn, порт 8000).

## Что делать

1. Создайте GitHub-репозиторий `retention-admin-frontend`.
2. Запушьте содержимое папки `retention-admin-frontend/` (корень нового repo).
3. Подключите **этот** репозиторий к Amvera frontend-проекту (root path пустой).

Инструкция: [../retention-admin-frontend/DEPLOY_AMVERA.md](../retention-admin-frontend/DEPLOY_AMVERA.md)

Скрипт публикации: `scripts/publish-retention-admin-frontend.ps1`
