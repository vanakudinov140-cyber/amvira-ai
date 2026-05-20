# Appointment Lifecycle → WhatsApp Rollout Notes

Scope: production-ready appointment lifecycle messaging only.

Lifecycle events:

```text
appointment_created
appointment_rescheduled
appointment_cancelled
→ deterministic FlowSell WhatsApp templates
```

This document does not enable scheduler, reminders, campaigns, batches, webhooks,
AI conversations, retention automation, or moderation automation.

---

## Current Status

| Layer | Status |
|-------|--------|
| Template catalog | ready |
| Placeholder rendering | ready |
| Payload validation | ready |
| Dry-run preview | ready |
| Controlled single send | ready |
| Scheduler automation | not enabled |
| Webhooks | not enabled |
| Batch sends | not enabled |

---

## Production Templates

### appointment_rescheduled_template

```text
{client_name}, здравствуйте!

Ваша запись перенесена 🔄

Услуга: {service_name}
Новые дата и время: {appointment_date} в {appointment_time}
Мастер: {master_name}

Проверить детали или изменить запись можно по ссылке:
{booking_link}

Спасибо за понимание. До встречи!
```

Required placeholders:

- `{client_name}`
- `{service_name}`
- `{appointment_date}`
- `{appointment_time}`
- `{master_name}`
- `{booking_link}`

### appointment_cancelled_template

```text
{client_name}, здравствуйте!

Ваша запись отменена ✅

Услуга: {service_name}
Дата и время: {appointment_date} в {appointment_time}

Если захотите выбрать новое время, записаться можно здесь:
{booking_link}

Будем рады видеть вас в салоне!
```

Required placeholders:

- `{client_name}`
- `{service_name}`
- `{appointment_date}`
- `{appointment_time}`
- `{booking_link}`

---

## Manual Controlled Flow

Use only the existing manual endpoints:

```http
POST /test/render-template
POST /test/send-preview
POST /test/send-real
```

Allowed events for this rollout:

```text
appointment_created
appointment_rescheduled
appointment_cancelled
```

Do **not** use:

- `POST /messages/send-pending`
- scheduler endpoints
- campaign tools
- webhook-triggered sends
- loops
- bulk scripts

---

## Safe Rollout Procedure

### 1. Keep safe defaults

```env
FLOWSELL_DRY_RUN=true
TEST_MODE=true
```

### 2. Render each event

```http
POST /test/render-template
Content-Type: application/json

{
  "event": "appointment_rescheduled",
  "values": {
    "client_name": "Анна",
    "service_name": "Окрашивание",
    "appointment_date": "22 мая",
    "appointment_time": "14:30",
    "master_name": "Мария",
    "booking_link": "<actual_crm_booking_link>"
  }
}
```

Repeat for:

```text
appointment_cancelled
```

Check:

- text is readable on mobile;
- line breaks are preserved;
- no raw placeholders remain;
- CTA link is correct;
- emoji renders correctly;
- tone is calm and client-friendly.

### 3. Preview payload

```http
POST /test/send-preview
```

Required:

```json
{
  "valid": true,
  "validation_errors": [],
  "chat_id": "79XXXXXXXXX@c.us"
}
```

### 4. Controlled single send

For a short controlled window only:

```env
FLOWSELL_DRY_RUN=false
TEST_MODE=false
```

Call exactly one request:

```http
POST /test/send-real
```

Send order recommendation:

1. Internal number: `appointment_rescheduled`
2. Internal number: `appointment_cancelled`
3. One real client only after manual approval of copy and formatting

### 5. Rollback immediately

```env
FLOWSELL_DRY_RUN=true
TEST_MODE=true
```

Re-run `POST /test/send-real` and confirm:

```json
{
  "dry_run": true,
  "sent": false
}
```

---

## Logs To Check

Dry-run path:

```text
flowsell send-preview dry-run event=appointment_rescheduled
flowsell send-preview dry-run event=appointment_cancelled
```

Controlled send path:

```text
flowsell controlled-send provider=flowsell dry_run=false
flowsell send ok idMessage=...
flowsell controlled-send finished sent=True
```

Rollback path:

```text
FLOWSELL_DRY_RUN=true: provider call skipped
```

---

## Rollback / Kill Switch

Immediate stop:

```env
FLOWSELL_DRY_RUN=true
TEST_MODE=true
```

Optional extra stop:

- remove `FLOWSELL_API_KEY` from env;
- do not call `/test/send-real`;
- do not call `/messages/send-pending`;
- keep scheduler, webhooks, campaigns, and batch scripts disabled.

---

## Safest Rollout Path

1. Approve final copy with the business owner.
2. Dry-run all three appointment lifecycle events.
3. Send only to internal numbers first.
4. Confirm WhatsApp formatting on real devices.
5. Send one real lifecycle message manually.
6. Return env to dry-run immediately.
7. Keep lifecycle sends manual until a separate task approves automation.

---

## Out Of Scope

- Scheduler
- Reminders
- Review funnels
- Retention automation
- Campaigns
- Batch sends
- AI conversations
- Webhooks
- DB schema changes
