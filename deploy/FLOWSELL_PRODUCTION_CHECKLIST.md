# FlowSell Production/Staging Checklist

Operational runbook before the first real FlowSell send.

Scope: **single controlled test send only**. No scheduler rollout, no batches,
no campaigns, no moderation auto-approval.

---

## 1. Architecture Flow

```text
event
→ template mapping
→ placeholder renderer
→ validation
→ dry-run orchestration
→ controlled send adapter
→ FlowSell provider (only if all safety gates pass)
```

Code map:

| Step | Module |
|------|--------|
| Template catalog | `backend/app/integrations/flowsell/templates/catalog.json` |
| Placeholder render | `backend/app/integrations/flowsell/templates/renderer.py` |
| Payload preview / validation | `backend/app/integrations/flowsell/orchestration.py` |
| Controlled send | `backend/app/integrations/flowsell/send_adapter.py` |
| Provider HTTP call | `backend/app/integrations/flowsell/client.py` |
| Manual endpoints | `backend/app/api/routes/test_flowsell.py` |

---

## 2. Hard Rules

- Only **one phone number** for the first send.
- No `POST /messages/send-pending` during first-send validation.
- No batch sends.
- No scheduler rollout.
- No campaigns.
- No incoming webhooks.
- No AI conversations.
- No auto-booking.
- No moderation auto-approval.
- Keep rollback variables ready before enabling real send.

---

## 3. Credentials Preparation

In FlowSell cabinet:

1. Create / choose WhatsApp account instance.
2. Authorize the instance via QR in WhatsApp Business.
3. Copy:
   - `idInstance`
   - `apiTokenInstance`

Set in staging/controlled backend env:

```env
FLOWSELL_API_BASE_URL=https://dev.flowsell.me/api/v1
FLOWSELL_INSTANCE_ID=<idInstance>
FLOWSELL_API_KEY=<apiTokenInstance>
```

Do **not** commit credentials. Use Amvera Variables / Secrets or local `.env`.

---

## 4. Safety Env Checklist

Before any real send:

| Variable | Dry-run/staging default | First real single send |
|----------|--------------------------|------------------------|
| `FLOWSELL_DRY_RUN` | `true` | `false` |
| `TEST_MODE` | `true` | `false` only for controlled single send |
| `FLOWSELL_INSTANCE_ID` | set | set |
| `FLOWSELL_API_KEY` | set | set |
| `SEND_PENDING_LIMIT` | unchanged | unchanged |
| `SCHEDULER_AUTOMATION_ENABLED` | unchanged | unchanged |

Safety gates in code require all of these for real provider call:

```text
FLOWSELL_DRY_RUN=false
TEST_MODE=false
FLOWSELL_INSTANCE_ID is set
FLOWSELL_API_KEY is set
validation_errors == []
```

If any gate fails, the adapter returns `sent=false` with warnings and does not
call FlowSell.

---

## 5. Pre-flight Checks

### 5.1 Backend health

```http
GET /health
GET /health/db
```

Expected:

```json
{"status":"ok"}
{"status":"ok","database":"connected"}
```

### 5.2 Render check (no phone, no send)

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

Check:

- `template` is correct.
- `rendered_text` has no broken placeholders.
- `missing_placeholders` is acceptable (prefer `[]`).

### 5.3 Send preview (payload validation, no send)

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

Expected:

```json
{
  "dry_run": true,
  "valid": true,
  "chat_id": "79991234567@c.us",
  "validation_errors": [],
  "validation_warnings": []
}
```

### 5.4 Controlled adapter check while dry-run is still enabled

```http
POST /test/send-real
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

Expected while `FLOWSELL_DRY_RUN=true`:

```json
{
  "dry_run": true,
  "sent": false,
  "provider": "flowsell",
  "message_id": null,
  "warnings": ["FLOWSELL_DRY_RUN=true: provider call skipped"]
}
```

---

## 6. First Real Send Procedure

Use staging or a controlled production maintenance window.

### Step 1 — confirm recipient

- One known internal/test phone number only.
- Confirm WhatsApp is available on the number.
- Confirm the recipient expects a message.

### Step 2 — verify payload

Run:

1. `POST /test/render-template`
2. `POST /test/send-preview`
3. `POST /test/send-real` with `FLOWSELL_DRY_RUN=true`

Proceed only if:

- `validation_errors=[]`
- `chat_id` is correct.
- `rendered_text` is approved.
- No unexpected placeholders remain.

### Step 3 — enable real single send

Set:

```env
FLOWSELL_DRY_RUN=false
TEST_MODE=false
```

Restart/redeploy backend if the platform requires env reload.

### Step 4 — send one message

Call **only**:

```http
POST /test/send-real
```

Do not call:

- `POST /messages/send-pending`
- scheduler endpoints
- any batch/campaign flow

Expected success:

```json
{
  "dry_run": false,
  "sent": true,
  "provider": "flowsell",
  "message_id": "...",
  "chat_id": "79991234567@c.us",
  "validation_errors": [],
  "warnings": []
}
```

### Step 5 — verify delivery

Check:

- Recipient received WhatsApp message.
- Text formatting is correct.
- FlowSell cabinet shows outgoing message.
- Backend logs include:
  - `flowsell controlled-send provider=flowsell dry_run=false`
  - `flowsell send ok idMessage=...`

### Step 6 — rollback immediately

Set:

```env
FLOWSELL_DRY_RUN=true
TEST_MODE=true
```

Restart/redeploy backend if needed.

Run `POST /test/send-real` again and verify:

```json
{
  "dry_run": true,
  "sent": false
}
```

---

## 7. Rollback Procedure

Immediate rollback:

```env
FLOWSELL_DRY_RUN=true
TEST_MODE=true
```

What happens after rollback:

- `send_adapter.py` skips provider calls.
- `FlowsellService` keeps TEST_MODE behavior.
- Real FlowSell messages stop.
- Dry-run previews still work.

To stop any real sends:

1. Set `FLOWSELL_DRY_RUN=true`.
2. Set `TEST_MODE=true`.
3. Keep scheduler rollout disabled / unchanged.
4. Do not call `/messages/send-pending`.
5. If needed, temporarily remove `FLOWSELL_API_KEY` from environment.

---

## 8. Validation Checklist

Before first send, confirm:

- [ ] `event` maps to expected template.
- [ ] `service_type` maps correctly or falls back intentionally.
- [ ] `phone` becomes correct `chat_id`.
- [ ] `rendered_text` length is under 4096.
- [ ] `validation_errors=[]`.
- [ ] `missing_placeholders=[]` or fallbacks are acceptable.
- [ ] Message text is approved by a human.
- [ ] `dry_run=true` preview was checked before real send.

---

## 9. Formatting Checklist

- [ ] Client name is correct.
- [ ] Service name is correct.
- [ ] Date and time are human-readable.
- [ ] Master name is correct or fallback is acceptable.
- [ ] Booking/review link is correct.
- [ ] No raw placeholders like `{client_name}` remain.
- [ ] No AI-generated or unapproved copy is used.
- [ ] Message is appropriate for WhatsApp.

---

## 10. Logging Checklist

Look for these log fields/messages:

- `event`
- `template_id`
- `service_type`
- `chat_id`
- `dry_run`
- `validation errors`
- `validation warnings`
- `provider=flowsell`
- `idMessage` on success
- provider error preview on failure

Do not log full API tokens.

---

## 11. Troubleshooting

### Invalid credentials

Symptoms:

- `sent=false`
- provider response has `API 401: Unauthorized`
- FlowSell cabinet token mismatch

Actions:

1. Verify `FLOWSELL_INSTANCE_ID`.
2. Verify `FLOWSELL_API_KEY`.
3. Re-copy `apiTokenInstance`.
4. Keep `FLOWSELL_DRY_RUN=true` until fixed.

### Provider unavailable / network failure

Symptoms:

- `provider_response_preview` contains HTTP/network error.
- Logs show `flowsell network error`.

Actions:

1. Check FlowSell status / cabinet.
2. Retry only one manual send after provider is stable.
3. Do not run batches.

### Invalid phone format

Symptoms:

- `validation_errors` contains invalid phone / `chatId` issue.

Actions:

1. Use international digits: `79991234567`.
2. Avoid spaces/symbols if debugging.
3. Re-run `/test/send-preview`.

### Missing placeholders

Symptoms:

- `missing_placeholders` non-empty.
- `validation_warnings` mention fallback.

Actions:

1. Confirm values in request body.
2. Check template required placeholders.
3. Approve fallback text manually before send.

### Validation errors

Symptoms:

- `validation_errors` non-empty.
- Adapter returns `sent=false`.

Actions:

1. Fix request body.
2. Re-run `/test/send-preview`.
3. Proceed only when errors are empty.

### FlowSell API errors

Symptoms:

- HTTP error or response body `{ "code": ..., "description": "..." }`.

Actions:

1. Read `provider_response_preview`.
2. Check credentials and instance authorization.
3. Confirm QR session is active.
4. Roll back to `FLOWSELL_DRY_RUN=true`.

### Message formatting issues

Symptoms:

- Recipient receives text with bad date/time/link/name.

Actions:

1. Roll back to dry-run.
2. Fix template values or catalog.
3. Re-run render and preview.
4. Do not send another real message until copy is approved.

---

## 12. Staging Recommendations

- Use a dedicated test phone.
- Use a dedicated FlowSell instance if possible.
- Keep `FLOWSELL_DRY_RUN=true` except during the exact first send window.
- Keep `TEST_MODE=true` except during the exact controlled send window.
- Do not call batch endpoints.
- Do not enable scheduler rollout.
- Do not change moderation automation.
- Do not test with real client phones until the internal test succeeds.

---

## 13. Success Criteria

First send is considered successful only when:

- [ ] One message was sent through `/test/send-real`.
- [ ] Response has `sent=true`.
- [ ] Response includes `message_id`.
- [ ] Recipient confirms delivery.
- [ ] Message formatting is correct.
- [ ] Logs contain expected provider success.
- [ ] System is rolled back to `FLOWSELL_DRY_RUN=true` and `TEST_MODE=true`.
