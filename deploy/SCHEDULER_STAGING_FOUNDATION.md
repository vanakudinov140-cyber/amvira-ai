# Scheduler Staging Foundation

Scope: staging-only scheduler foundation with no active execution.

This document does **not** enable production auto sends, cron execution, mass
processing, queues, workers, retries, AI orchestration, or autonomous behavior.

---

## Runtime Surface

Read-only status endpoint:

```http
GET /scheduler/staging-status
```

This endpoint only reports configuration and safety guards. It does not start
jobs, process records, call FlowSell, or enqueue work.

Manual simulation endpoint:

```http
POST /scheduler/dry-run-preview
```

This endpoint simulates a single future scheduler decision. It returns matched
flow, service category, delay rule, template id, recipient source and active
guards. It does not render templates, call the send adapter, call FlowSell, or
start background execution.

Human-friendly planner preview page:

```http
GET /scheduler/planner-preview
```

This page calls `POST /scheduler/dry-run-preview` and displays the simulation in
readable cards. It has visible `DRY RUN ONLY`, `NO REAL SENDS` and
`PROVIDER DISABLED` badges.

---

## Config Layer

| Variable | Safe default | Purpose |
|----------|--------------|---------|
| `SCHEDULER_STAGING_FOUNDATION_ENABLED` | `false` | Foundation flag only; no execution |
| `SCHEDULER_STAGING_MODE` | `true` | Staging safety mode |
| `SCHEDULER_STAGING_MAX_RECORDS` | `1` | Hard limit for future staging cycles |
| `SCHEDULER_STAGING_REQUIRE_DRY_RUN` | `true` | Requires `FLOWSELL_DRY_RUN=true` |
| `SCHEDULER_STAGING_ONLY_TEST_RECIPIENTS` | `true` | Only `TEST_RECIPIENTS` may be used |

`SCHEDULER_STAGING_MAX_RECORDS` intentionally rejects values other than `1`.

---

## Active Safety Guards

Current status always reports:

```text
active_execution_enabled=false
background_loop_enabled=false
max_records_per_cycle=1
only_test_recipients=true
dry_run_required=true
no queues/workers/retry loops
controlled send adapter remains the only send path
```

---

## Future Reminder Execution

Future reminder scheduler work should be a separate staging task:

```text
select one upcoming appointment
→ build reminder event
→ render template
→ send-preview validation
→ controlled send adapter
→ provider call only after explicit approval
```

Start only with:

```env
FLOWSELL_DRY_RUN=true
TEST_MODE=true
SCHEDULER_STAGING_MAX_RECORDS=1
```

---

## Future Delayed Review Execution

Future review scheduler work should use the read-only review registry:

```text
completed appointment
→ match service category
→ select review event and delay
→ build preview
→ validate
→ controlled send adapter
```

No review event currently triggers automatically.

---

## Dry-Run Planner Response

Example request:

```json
{
  "flow_type": "review",
  "service_name": "Окрашивание волос",
  "is_new_client": false,
  "client_phone": "79991234567"
}
```

Example response shape:

```json
{
  "dry_run": true,
  "would_send": true,
  "blocked_by_guard": false,
  "matched_flow": "review",
  "matched_category": "coloring",
  "matched_event": "review_coloring_3d",
  "template_id": "review_coloring_template",
  "delay_rule": {
    "delay_type": "days",
    "delay_value": 3,
    "description": "3 days after completed appointment"
  },
  "recipient_source": "TEST_RECIPIENTS[0]",
  "provider_access": false,
  "send_pipeline_called": false,
  "background_execution": false
}
```

Safety guard behavior:

- if `FLOWSELL_DRY_RUN=false`, `would_send=false`;
- if `TEST_RECIPIENTS` is empty, `would_send=false`;
- if no flow matches, `would_send=false`;
- max records is always one request / one simulated record.

---

## Rollback / Emergency Disable

Immediate stop:

```env
FLOWSELL_DRY_RUN=true
TEST_MODE=true
SCHEDULER_STAGING_FOUNDATION_ENABLED=false
SCHEDULER_AUTOMATION_ENABLED=false
```

Additional safe stops:

- remove `FLOWSELL_API_KEY`;
- do not call `/scheduler/run-now`;
- do not call `/messages/send-pending`;
- keep scheduler staging status read-only;
- do not add cron, queues, workers, retries, or batch scripts.

---

## Out Of Scope

- Production auto sends
- Active cron execution
- Background workers
- Queues
- Retries
- Mass processing
- AI orchestration
- Multi-user batch jobs
- Autonomous behavior
