# FlowSell API — интеграция для AI Retention System

Документация API: https://dev.flowsell.me/docs/

---

## 1. Авторизация

FlowSell **не использует** Bearer token на `/messages`.

Доступ к WhatsApp instance:

| Параметр | Где взять | Env в проекте |
|----------|-----------|---------------|
| `idInstance` | Кабинет FlowSell → WhatsApp account | `FLOWSELL_INSTANCE_ID` |
| `apiTokenInstance` | Там же / partner createInstance | `FLOWSELL_API_KEY` |

**Подготовка (кабинет):**

1. https://cabinet.flowsell.me — профиль и WhatsApp account  
2. Авторизация QR (WhatsApp Business на телефоне)  
3. Скопировать `idInstance` + `apiTokenInstance`

**HTTP:** credentials в **path URL**, не в Authorization header.

```
POST https://dev.flowsell.me/api/v1/waInstance{idInstance}/sendMessage/{apiTokenInstance}
```

---

## 2. Отправка текстового сообщения

**Endpoint:** [Send text](https://dev.flowsell.me/docs/api/sending/text/)

| Поле | Обязательно | Описание |
|------|-------------|----------|
| `chatId` | да | `79001234567@c.us` |
| `message` | да | Текст, до 4096 символов |

**Response (успех):**

```json
{ "idMessage": "3EB0C767D097B7C7C030" }
```

**Ошибка (может быть HTTP 200):**

```json
{ "code": 401, "description": "Unauthorized" }
```

---

## 3. curl — test send

```bash
export FLOWSELL_INSTANCE_ID="1101728000"
export FLOWSELL_API_KEY="your_apiTokenInstance"
export PHONE="79001234567"
export TEXT="Test from AI Retention"

curl -sS -X POST \
  "https://dev.flowsell.me/api/v1/waInstance${FLOWSELL_INSTANCE_ID}/sendMessage/${FLOWSELL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"chatId\":\"${PHONE}@c.us\",\"message\":\"${TEXT}\"}"
```

---

## 4. Python / Backend

**Модуль:** `backend/app/integrations/flowsell/`

| Файл | Назначение |
|------|------------|
| `client.py` | HTTP sendMessage, checkWhatsapp |
| `mapper.py` | phone → chatId, channel mapping |
| `orchestration.py` | Dry-run event → template → payload preview |
| `send_adapter.py` | Controlled single-message real-send adapter (safe by default) |
| `service.py` | send approved messages (batch) |
| `templates/` | JSON catalog, event/service mapper, safe placeholders |
| `exceptions.py` | FlowsellNotConfiguredError |

**CLI test:**

```bash
cd backend
set TEST_MODE=false
set FLOWSELL_INSTANCE_ID=...
set FLOWSELL_API_KEY=...
python scripts/test_flowsell_send.py --phone 79001234567 --message "Hello"
```

**FastAPI test (TEST_MODE=false):**

```http
POST /test/flowsell-send
Content-Type: application/json

{
  "phone": "79001234567",
  "message": "Test from retention API",
  "channel": "sms"
}
```

**Dry-run endpoints (no API calls, safe with TEST_MODE=true):**

```http
POST /test/render-template
Content-Type: application/json

{
  "event": "appointment_created",
  "service_type": "hair_coloring",
  "values": {
    "client_name": "Анна",
    "service_name": "Окрашивание",
    "appointment_date": "21 мая",
    "appointment_time": "12:00",
    "master_name": "Мария",
    "booking_link": "https://example.com/booking"
  }
}
```

```http
POST /test/send-preview
Content-Type: application/json

{
  "event": "appointment_created",
  "phone": "79991234567",
  "channel": "sms",
  "values": {
    "client_name": "Анна",
    "service_name": "Окрашивание",
    "appointment_date": "21 мая",
    "appointment_time": "12:00",
    "master_name": "Мария",
    "booking_link": "https://example.com/booking"
  }
}
```

Preview response:

```json
{
  "event": "appointment_created",
  "phone": "79991234567",
  "template": "appointment_created_template",
  "rendered_text": "...",
  "missing_placeholders": [],
  "dry_run": true,
  "channel": "sms",
  "delivery_channel": "whatsapp",
  "chat_id": "79991234567@c.us",
  "validation_errors": [],
  "validation_warnings": [],
  "valid": true
}
```

---

## 5. Env variables

| Variable | Required | Example |
|----------|----------|---------|
| `FLOWSELL_API_BASE_URL` | no | `https://dev.flowsell.me/api/v1` |
| `FLOWSELL_INSTANCE_ID` | yes (prod send) | `1101728000` |
| `FLOWSELL_API_KEY` | yes (prod send) | `c1b04745...` |
| `FLOWSELL_DRY_RUN` | no | `true` by default; must be `false` for controlled real send |
| `TEST_MODE` | — | `true` → FlowSell не вызывается, Telegram test |

`FLOWSELL_API_URL` — **устарело**, не используется новым клиентом.

---

## 6. Channel mapping (retention → FlowSell)

Retention хранит `channel`: `sms` | `telegram`.

FlowSell доставляет **только WhatsApp** по номеру `client.phone`:

- `sms` / `telegram` → WhatsApp `chatId` через `phone_to_chat_id()`
- Доставка не зависит от Telegram username

---

## 7. Template system (prepared, not wired to sends)

Модуль: `backend/app/integrations/flowsell/templates/`

| File | Purpose |
|------|---------|
| `catalog.json` | Каталог шаблонов без DB migration |
| `catalog.py` | Event → template и service_type → template |
| `renderer.py` | Безопасная замена `{placeholder}` без template engine |
| `models.py` | DB-ready dataclasses |

Категории:

- `reminders`
- `reviews`
- `appointment_created`
- `appointment_rescheduled`
- `appointment_cancelled`
- `aftercare`

Поддерживаемые placeholders:

- `{client_name}`
- `{service_name}`
- `{appointment_date}`
- `{appointment_time}`
- `{master_name}`
- `{booking_link}`

Примеры mapping:

| Input | Template |
|-------|----------|
| `event=appointment_created` | `appointment_created_template` |
| `event=appointment_cancelled` | `appointment_cancelled_template` |
| `event=review_request`, `service_type=hair_coloring` | `review_coloring_template` |
| `event=review_request`, `service_type=brows` | `review_brows_template` |
| `event=review_request`, unknown service | `review_default_template` |

Важно: система **не подключена** к scheduler, moderation pipeline или real send. Это инфраструктура для следующих задач P0/P1.

---

## 8. Dry-run send orchestration (prepared, no real sends)

Модуль: `backend/app/integrations/flowsell/orchestration.py`

Flow:

```text
event
→ template selection
→ placeholder render
→ payload preview
→ validation
→ structured logging
```

Проверки:

- phone → `chatId`
- supported channel
- rendered text is not empty
- rendered text length ≤ 4096
- missing placeholders are returned as warnings

Этот layer **не вызывает** `FlowsellClient` и не отправляет сообщения.

---

## 9. Controlled real-send adapter (prepared, manual only)

Модуль: `backend/app/integrations/flowsell/send_adapter.py`

Flow:

```text
event
→ template selection
→ render
→ validation
→ payload generation
→ optional real send
→ structured result
```

Safety gates for real provider call:

| Gate | Required |
|------|----------|
| `FLOWSELL_DRY_RUN` | `false` |
| `TEST_MODE` | `false` |
| `FLOWSELL_INSTANCE_ID` | configured |
| `FLOWSELL_API_KEY` | configured |
| validation errors | none |

If a gate fails, the adapter returns `sent=false` with warnings and does not crash.

Manual endpoint:

```http
POST /test/send-real
Content-Type: application/json

{
  "event": "appointment_created",
  "phone": "79991234567",
  "channel": "sms",
  "values": {
    "client_name": "Анна",
    "service_name": "Стрижка",
    "appointment_date": "21 мая",
    "appointment_time": "12:00",
    "master_name": "Мария",
    "booking_link": "https://example.com"
  }
}
```

Default response while `FLOWSELL_DRY_RUN=true`:

```json
{
  "dry_run": true,
  "sent": false,
  "provider": "flowsell",
  "message_id": null,
  "warnings": ["FLOWSELL_DRY_RUN=true: provider call skipped"]
}
```

This endpoint is for **single controlled tests only**. It is not connected to scheduler, batches, campaigns, or moderation auto-approval.

---

## 10. План следующих сценариев (не реализовано)

| Сценарий | FlowSell / внешнее | Приоритет |
|----------|-------------------|-----------|
| Напоминания о визите | sendMessage (готово) | P0 ✅ base |
| Запрос отзыва | sendMessage + template | P1 |
| Создание записи | YCLIENTS API + confirm WA | P2 |
| Перенос записи | YCLIENTS + notification | P2 |
| Отмена записи | YCLIENTS + notification | P2 |
| Входящие ответы | FlowSell webhooks → retention | P3 |
| AI-диалоги | — | out of scope |
| Visual workflow | — | out of scope |

**Webhooks:** https://dev.flowsell.me/docs/api/account/set-settings/

**Проверка WA на номере:** `POST .../checkWhatsapp/{token}` — реализовано в `FlowsellClient.check_whatsapp()`.

---

## 11. Checklist первого успешного send

- [ ] WhatsApp instance авторизован (QR в кабинете)
- [ ] `FLOWSELL_INSTANCE_ID` + `FLOWSELL_API_KEY` в Amvera
- [ ] `TEST_MODE=false` для реальной отправки
- [ ] curl или `scripts/test_flowsell_send.py` → `idMessage` в ответе
- [ ] `POST /test/flowsell-send` → `ok: true`
- [ ] Approve message → `POST /messages/send-pending` → status `sent`
