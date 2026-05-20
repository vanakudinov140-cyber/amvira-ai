# Appointment Created → WhatsApp Rollout Notes

Scope: first production-ready automation scenario **only**.

Scenario:

```text
appointment_created
→ appointment_created_template
→ FlowSell WhatsApp send
```

This document does not enable scheduler, campaigns, batches, or auto-booking.

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
| Batch sends | not enabled |

---

## Production Template

Template id: `appointment_created_template`

```text
{client_name}, здравствуйте!

Ваша запись подтверждена ✅

Услуга: {service_name}
Дата и время: {appointment_date} в {appointment_time}
Мастер: {master_name}

Если нужно изменить или отменить запись, используйте ссылку:
{booking_link}

До встречи в салоне!
```

Required placeholders:

- `{client_name}`
- `{service_name}`
- `{appointment_date}`
- `{appointment_time}`
- `{master_name}`
- `{booking_link}`

---

## Manual Controlled Flow

Use only:

```http
POST /test/render-template
POST /test/send-preview
POST /test/send-real
```

Do **not** use:

- `POST /messages/send-pending`
- scheduler endpoints
- campaigns
- loops
- bulk scripts

---

## Safe Rollout Procedure

### 1. Keep safe defaults

```env
FLOWSELL_DRY_RUN=true
TEST_MODE=true
```

### 2. Render template

```http
POST /test/render-template
Content-Type: application/json

{
  "event": "appointment_created",
  "values": {
    "client_name": "Анна",
    "service_name": "Окрашивание",
    "appointment_date": "21 мая",
    "appointment_time": "12:00",
    "master_name": "Мария",
    "booking_link": "<actual_crm_booking_link>"
  }
}
```

Check:

- text has clean spacing;
- no raw placeholders remain;
- CTA link is correct;
- emoji renders correctly.

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

Expected:

```json
{
  "sent": true,
  "provider": "flowsell",
  "message_id": "..."
}
```

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

Success path:

```text
flowsell send-preview dry-run event=appointment_created
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
- do not call `/messages/send-pending`.

---

## Production Rollout Recommendations

1. Start with internal/test numbers only.
2. Verify text formatting on real WhatsApp devices.
3. Keep sends manual until product owner approves the exact copy.
4. Do not connect to scheduler or appointment webhooks yet.
5. Add appointment data source only as a separate task.
6. Add per-salon copy/branding only after baseline delivery is stable.

---

## Out Of Scope

- Scheduler automation
- Mass sends
- Campaigns
- Incoming messages
- AI conversations
- Auto-booking
- DB schema changes
