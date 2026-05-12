# Пакет для сервера Amvera

Эта папка содержит готовый пакет для запуска VK-бота на сервере.

## Что внутри

- `main.py` — код бота (LongPoll).
- `requirements.txt` — зависимости Python.
- `.env.example` — пример переменных окружения.
- `Procfile` — запуск как worker (`python main.py`).
- `Dockerfile` — вариант контейнерного запуска.

## Быстрый деплой

1. Загрузите содержимое этой папки на сервер/в проект Amvera.
2. Установите переменные окружения по образцу из `.env.example`.
3. Запустите процесс:
   - через `Procfile` (worker), либо
   - через `Dockerfile`.

## Обязательные переменные

- `VK_GROUP_TOKEN`
- `VK_GROUP_ID`

## Рекомендуемые переменные

- `VK_ADMIN_IDS`
- `PD_POLICY_URL`
- `ADMIN_CONTACT_LINK`
- `DEFAULT_STAGE_WINNERS_COUNT`
- `REMINDER_INTERVAL_SEC`
- `USER_MESSAGE_RATE_LIMIT_SEC`

## Проверка после запуска

1. Откройте диалог с ботом в VK.
2. Отправьте `/start`.
3. Проверьте работу кнопок и админ-панели.
