# Деплой Admin Dashboard на Amvera

Отдельный Docker-проект: **nginx + статический SPA** на порту **80**.  
Backend API: `https://retention-v2-ivankudinov.amvera.io`

---

## 1. Создать проект в Amvera

1. **Приложения** → **Создать** → тип **Docker / Git**.
2. Имя, например: `retention-admin-ivankudinov`.
3. Подключить репозиторий `amvira-ai` (GitHub).
4. **Корень сборки (root path):** `admin-dashboard` — обязательно, иначе подтянется backend `Dockerfile` из корня репо.
5. Ветка: `main`.

Amvera подхватит `admin-dashboard/amvera.yml` и `admin-dashboard/Dockerfile`.

---

## 2. Порты

| Параметр | Значение |
|----------|----------|
| `containerPort` | 80 |
| `servicePort` | 80 |

---

## 3. Переменные окружения

Для production-сборки URL API зашивается в образ через `Dockerfile` (`ARG VITE_API_URL`).  
При необходимости переопределите в Amvera **build args** (если поддерживаются) или измените `Dockerfile`.

Runtime-переменные для nginx **не нужны**.

---

## 4. CORS

Backend уже разрешает:

- `allow_origin_regex`: `https://.*\.amvera\.(io|app)`
- локальные порты Vite для разработки

После деплоя фронта origin вида `https://retention-admin-ivankudinov.amvera.app` работает без правок backend.

Опционально добавьте в backend `CORS_ORIGINS` точный URL дашборда.

---

## 5. Проверка после деплоя

| Проверка | URL / действие |
|----------|----------------|
| Главная | `https://<проект>.amvera.app/` |
| Кандидаты | `.../candidates` |
| Модерация | `.../pending` |
| Синхронизация | `.../sync` |
| Прямой refresh | F5 на любом маршруте → 200, не 404 |
| API badge | в шапке «API online» |
| Данные | карточки аналитики, таблицы кандидатов |

Локально перед push:

```bash
cd admin-dashboard
npm run build
docker build -t retention-admin:test .
docker run --rm -p 8080:80 retention-admin:test
# http://127.0.0.1:8080/candidates → index.html
```

---

## 6. Ожидаемый URL

После успешного деплоя:

**https://retention-admin-ivankudinov.amvera.app**

(или домен `.amvera.io`, если так настроен проект в панели Amvera)

---

## 7. Troubleshooting

| Симптом | Решение |
|---------|---------|
| 503 / приложение не стартует | Проверить root path = `admin-dashboard`, логи сборки Docker |
| Собирается backend вместо SPA | Root path должен указывать на `admin-dashboard/` |
| API offline в шапке | Проверить `https://retention-v2-ivankudinov.amvera.io/health` |
| CORS error в консоли | Origin должен быть `*.amvera.app` или `*.amvera.io` |
| 404 на `/candidates` после F5 | Проверить `nginx.conf` → `try_files ... /index.html` |
