# Changelog — AI Retention System

Формат: по этапам и датам. Только **завершённые** изменения с кратким manual QA.

Не дублировать git history — здесь product/engineering summary для команды и AI-ассистентов.

---

## [Unreleased]

### Added
- Production-safe FlowSell template infrastructure:
  - `backend/app/integrations/flowsell/templates/catalog.json`
  - safe placeholder renderer (`{client_name}`, `{service_name}`, `{appointment_date}`, `{appointment_time}`, `{master_name}`, `{booking_link}`)
  - event → template mapping and service_type → review template mapping
  - tests for rendering, fallback behavior, and catalog selection
- Dry-run FlowSell send orchestration:
  - `backend/app/integrations/flowsell/orchestration.py`
  - `POST /test/render-template`
  - `POST /test/send-preview`
  - payload preview with validation errors/warnings and no real API calls
- Controlled FlowSell real-send foundation:
  - `backend/app/integrations/flowsell/send_adapter.py`
  - `FLOWSELL_DRY_RUN=true` default safety gate
  - `POST /test/send-real` for single controlled send attempts only
  - graceful warnings when dry-run is enabled, `TEST_MODE=true`, credentials are missing, or validation fails
- Operational FlowSell first-send checklist:
  - `deploy/FLOWSELL_PRODUCTION_CHECKLIST.md`
  - credentials/env checks, dry-run verification, first-send procedure, rollback, troubleshooting, staging rules
- Production polishing for `appointment_created`:
  - cleaner WhatsApp formatting with line breaks, CTA and friendly closing
  - rollout notes in `deploy/APPOINTMENT_CREATED_ROLLOUT.md`
- Production polishing for appointment lifecycle:
  - WhatsApp-ready `appointment_rescheduled_template` and `appointment_cancelled_template`
  - manual controlled rollout notes in `deploy/APPOINTMENT_LIFECYCLE_ROLLOUT.md`
- Internal FlowSell demo/testing UI:
  - lightweight `/test/flowsell-demo` page for manual single WhatsApp lifecycle sends
  - uses existing `/test/send-real` controlled pipeline without duplicating send logic
  - shows loading, success/error state, sent/dry-run status, message id, warnings, validation errors and provider response preview
- Customer-friendly demo UI polish:
  - Russian labels and scenario names for lifecycle/reminder test sends
  - reminder scenarios `reminder_24h` and `reminder_2h` in `/test/flowsell-demo`
  - hides raw JSON/debug output and shows readable send status, message preview, warnings and validation errors
- Production reminder template polishing:
  - replaced `reminder_24h_template` and `reminder_2h_template` with customer-approved “ВНЕ РАМОК” WhatsApp copy
  - preserved deterministic placeholders, spacing, emoji and dry-run-only rollout safety
- WhatsApp link normalization in reminder templates:
  - bare `clck.ru`, `instagram.com`, `t.me`, `vk.com` links prefixed with `https://` for clickable URLs
  - links kept on standalone lines after labels (not inside brackets or glued to emoji)
- Review flow foundation:
  - added deterministic `review_new_client_60m_template` with customer-approved “ВНЕ РАМОК” WhatsApp copy
  - dry-run/manual template only; no scheduler, delayed jobs, queues, retry logic, segmentation or automation rollout
- Manual review testing support:
  - added `review_new_client_60m` to `/test/flowsell-demo` with the label “Запрос отзыва новому клиенту”
  - uses existing controlled send pipeline only
- Delayed review architecture foundation:
  - read-only registry for `review_new_client_60m`, `review_haircut_3d`, `review_coloring_3d`, `review_brows_7d`, `review_care_7d`, `review_makeup_7d`, `review_styling_7d`
  - service category matching foundation for haircut, coloring, brows, care, makeup and styling
  - required by scheduler dry-run planner imports; no scheduler, cron, queues, retry loops, workers or automation enabled
- Scheduler staging foundation:
  - read-only staging status endpoint `GET /scheduler/staging-status`
  - config layer for staging mode, dry-run enforcement, TEST_RECIPIENTS-only guard and max 1 record per future cycle
  - docs in `deploy/SCHEDULER_STAGING_FOUNDATION.md`; no cron, jobs, queues, workers, retries or automatic sends enabled
- Scheduler dry-run planner foundation:
  - manual simulation endpoint `POST /scheduler/dry-run-preview`
  - returns matched flow/category/event/template/delay/recipient guard data without render, send adapter, provider access or background execution
  - hard guards for `FLOWSELL_DRY_RUN`, `TEST_RECIPIENTS` and max one simulated record
- Manual planner verification UI:
  - human-friendly page `GET /scheduler/planner-preview`
  - uses existing `POST /scheduler/dry-run-preview` only and shows readable flow/category/template/delay/safety guard output
  - visible `DRY RUN ONLY`, `NO REAL SENDS`, `PROVIDER DISABLED` badges

### Notes
- Real sends remain disabled by default (`FLOWSELL_DRY_RUN=true`, `TEST_MODE` unchanged).
- No scheduler, moderation pipeline, AI generation, DB schema, or deploy changes.

### Planned (see TASKS/)
- P0: FlowSell prod test send, template mapping hardening, reminders
- P1–P4: см. `ROADMAP.md`

---

## 2026-05 — Engineering workflow

### Added
- `project-management/` — ROADMAP, PROJECT_RULES, TASKS, PROMPTS, CHANGELOG

### Notes
- No production behavior changes in this release.

---

## 2026-05 — FlowSell integration (code)

### Added
- `backend/app/integrations/flowsell/mapper.py` — phone → chatId
- `deploy/FLOWSELL_INTEGRATION.md` — API docs summary
- `POST /test/flowsell-send`, `scripts/test_flowsell_send.py`
- Env: `FLOWSELL_INSTANCE_ID`, `FLOWSELL_API_BASE_URL`

### Changed
- `FlowsellClient` — real FlowSell `sendMessage` endpoint (was incorrect `/messages` + Bearer)

### Manual QA
- [ ] curl test send with real credentials
- [ ] `POST /test/flowsell-send` with `TEST_MODE=false`
- [ ] Approve + `POST /messages/send-pending` (staging only)

---

## 2026-05 — Frontend standalone + Amvera env

### Added
- Repo `retention-admin-frontend` (GitHub standalone)
- `retention-admin-frontend/` export in monorepo
- `deploy/AMVERA_ENV.md`, DATABASE_URL production guards

### Manual QA
- [ ] Amvera frontend project → repo `retention-admin-frontend`, empty root path
- [ ] Build logs: nginx, not uvicorn
- [ ] Dashboard loads API data

---

## Template for new entries

```markdown
## YYYY-MM-DD — Short title

### Added
- ...

### Changed
- ...

### Fixed
- ...

### Manual QA
- [ ] ...
```
