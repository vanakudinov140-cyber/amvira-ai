"""Управление retention automation scheduler."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.scheduler.dry_run_planner import PlannerInput, build_scheduler_dry_run_plan
from app.scheduler import setup as scheduler_setup
from app.scheduler.staging_foundation import get_scheduler_staging_status

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

PLANNER_PREVIEW_HTML = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Проверка логики планировщика</title>
  <style>
    :root {
      --bg: #f6f8fc;
      --card: #ffffff;
      --text: #172033;
      --muted: #667085;
      --border: #dfe5ef;
      --primary: #2563eb;
      --success: #047857;
      --danger: #b91c1c;
      --badge: #eef4ff;
      --badge-border: #c7d7fe;
      --warning: #fff7ed;
      --warning-border: #fed7aa;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: radial-gradient(circle at top left, #eaf1ff, transparent 34%), var(--bg);
      color: var(--text);
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }
    main {
      width: min(980px, calc(100% - 28px));
      margin: 28px auto;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 22px;
      box-shadow: 0 20px 55px rgba(23, 32, 51, 0.08);
      padding: 26px;
    }
    h1 { margin: 0 0 8px; font-size: clamp(24px, 4vw, 34px); letter-spacing: -0.03em; }
    h2 { margin: 22px 0 10px; font-size: 18px; }
    p { margin: 0; color: var(--muted); }
    .badges {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin: 18px 0;
    }
    .badge {
      border: 1px solid var(--badge-border);
      border-radius: 999px;
      background: var(--badge);
      color: #1e3a8a;
      font-weight: 800;
      padding: 8px 12px;
      font-size: 13px;
    }
    .notice {
      margin: 18px 0;
      padding: 14px 16px;
      border-radius: 16px;
      background: var(--warning);
      border: 1px solid var(--warning-border);
      color: #7c2d12;
    }
    form {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      margin-top: 20px;
    }
    label {
      display: grid;
      gap: 7px;
      font-weight: 650;
      color: #263246;
    }
    input, select {
      width: 100%;
      min-height: 46px;
      border: 1px solid var(--border);
      border-radius: 13px;
      padding: 11px 13px;
      font: inherit;
      color: var(--text);
      background: #fff;
    }
    input:focus, select:focus {
      outline: 3px solid rgba(37, 99, 235, 0.15);
      border-color: var(--primary);
    }
    .help {
      color: var(--muted);
      font-size: 13px;
      font-weight: 500;
    }
    .actions {
      grid-column: 1 / -1;
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
      margin-top: 4px;
    }
    button {
      border: 0;
      border-radius: 13px;
      padding: 13px 20px;
      background: var(--primary);
      color: #fff;
      cursor: pointer;
      font: inherit;
      font-weight: 750;
      min-height: 48px;
    }
    button:disabled { opacity: 0.65; cursor: wait; }
    .status {
      min-height: 24px;
      font-weight: 750;
    }
    .status.error { color: var(--danger); }
    .status.success { color: var(--success); }
    .result {
      margin-top: 22px;
      display: none;
      border-top: 1px solid var(--border);
      padding-top: 20px;
    }
    .result.visible { display: block; }
    .summary {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin: 14px 0;
    }
    .metric, .details {
      border: 1px solid var(--border);
      border-radius: 15px;
      padding: 13px;
      background: #fbfcff;
    }
    .metric span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 5px;
    }
    .details {
      display: grid;
      gap: 8px;
      margin-top: 12px;
    }
    .empty { color: var(--muted); }
    ul { margin: 8px 0 0; padding-left: 20px; }
    @media (max-width: 760px) {
      main { width: min(100% - 20px, 980px); margin: 10px auto; }
      .card { padding: 18px; border-radius: 18px; }
      form, .summary { grid-template-columns: 1fr; }
      button { width: 100%; }
      .actions { align-items: stretch; }
    }
  </style>
</head>
<body>
  <main>
    <section class="card">
      <h1>Проверка логики планировщика</h1>
      <p>Безопасный preview: показывает, какой сценарий был бы выбран для одной записи. Сообщения не отправляются.</p>

      <div class="badges">
        <div class="badge">DRY RUN ONLY</div>
        <div class="badge">NO REAL SENDS</div>
        <div class="badge">PROVIDER DISABLED</div>
      </div>

      <div class="notice">
        Эта страница не запускает cron, фоновые задачи, очереди или отправки. Она вызывает только simulation endpoint.
      </div>

      <form id="plannerForm">
        <label>
          Тип проверки
          <select id="flow_type" name="flow_type" required>
            <option value="review">Отзыв после визита</option>
            <option value="reminder">Напоминание о визите</option>
          </select>
        </label>
        <label>
          Услуга
          <input id="service_name" name="service_name" value="Окрашивание волос" required />
          <span class="help">Например: стрижка, окрашивание, брови, уход, макияж, укладка.</span>
        </label>
        <label>
          Номер клиента
          <input id="client_phone" name="client_phone" inputmode="tel" placeholder="79991234567" />
          <span class="help">Используется только для preview. Получатель берётся из TEST_RECIPIENTS.</span>
        </label>
        <label>
          Тип напоминания
          <select id="reminder_kind" name="reminder_kind">
            <option value="24h">За 24 часа</option>
            <option value="2h">За 2 часа</option>
          </select>
        </label>
        <label>
          ID записи
          <input id="record_id" name="record_id" placeholder="demo-record-1" />
        </label>
        <label>
          Клиент новый?
          <select id="is_new_client" name="is_new_client">
            <option value="false">Нет</option>
            <option value="true">Да</option>
          </select>
        </label>
        <div class="actions">
          <button id="submitButton" type="submit">Показать preview</button>
          <div id="status" class="status" aria-live="polite"></div>
        </div>
      </form>

      <section id="result" class="result">
        <h2>Результат preview</h2>
        <div class="summary">
          <div class="metric"><span>Найден сценарий</span><strong id="matchedEvent">-</strong></div>
          <div class="metric"><span>Категория услуги</span><strong id="matchedCategory">-</strong></div>
          <div class="metric"><span>Выбран шаблон</span><strong id="templateId">-</strong></div>
          <div class="metric"><span>Правило задержки</span><strong id="delayRule">-</strong></div>
          <div class="metric"><span>Dry-run режим</span><strong id="dryRun">-</strong></div>
          <div class="metric"><span>Отправка заблокирована</span><strong id="blocked">-</strong></div>
        </div>
        <h2>Почему выбран этот flow</h2>
        <div id="reasons" class="details"></div>
        <h2>Safety guards</h2>
        <div id="guards" class="details"></div>
      </section>
    </section>
  </main>

  <script>
    const form = document.getElementById("plannerForm");
    const button = document.getElementById("submitButton");
    const statusNode = document.getElementById("status");
    const resultNode = document.getElementById("result");
    const yesNo = (value) => value ? "Да" : "Нет";
    const getValue = (id) => document.getElementById(id).value.trim();

    const setStatus = (message, kind = "") => {
      statusNode.textContent = message;
      statusNode.className = `status ${kind}`;
    };

    const renderList = (items, emptyText = "нет") => {
      if (!items || items.length === 0) {
        return `<span class="empty">${emptyText}</span>`;
      }
      return `<ul>${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;
    };

    const delayText = (delayRule) => {
      if (!delayRule) return "-";
      if (delayRule.delay_type === "days") {
        return `${delayRule.delay_value} дн. после визита`;
      }
      if (delayRule.delay_type === "minutes") {
        return `${delayRule.delay_value} мин. после визита`;
      }
      if (delayRule.delay_type === "hours_before") {
        return `за ${delayRule.delay_value} ч. до визита`;
      }
      return delayRule.description || "-";
    };

    const renderResult = (data) => {
      document.getElementById("matchedEvent").textContent = data.matched_event || "-";
      document.getElementById("matchedCategory").textContent = data.matched_category || "-";
      document.getElementById("templateId").textContent = data.template_id || "-";
      document.getElementById("delayRule").textContent = delayText(data.delay_rule);
      document.getElementById("dryRun").textContent = yesNo(data.dry_run);
      document.getElementById("blocked").textContent = yesNo(data.blocked_by_guard);

      document.getElementById("reasons").innerHTML = [
        `<div><strong>Причины:</strong>${renderList(data.reasons)}</div>`,
        `<div><strong>Получатель:</strong> ${data.selected_recipient || "не выбран"} (${data.recipient_source})</div>`,
        `<div><strong>Будет отправлено в реальности:</strong> Нет, это только preview.</div>`
      ].join("");

      document.getElementById("guards").innerHTML = [
        `<div><strong>Ошибки guard:</strong>${renderList(data.guard_errors)}</div>`,
        `<div><strong>Активные ограничения:</strong>${renderList(data.safety_guards)}</div>`,
        `<div><strong>Provider access:</strong> ${yesNo(data.provider_access)}</div>`,
        `<div><strong>Send pipeline called:</strong> ${yesNo(data.send_pipeline_called)}</div>`,
        `<div><strong>Background execution:</strong> ${yesNo(data.background_execution)}</div>`
      ].join("");

      resultNode.classList.add("visible");
    };

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = {
        flow_type: getValue("flow_type"),
        service_name: getValue("service_name"),
        client_phone: getValue("client_phone") || null,
        record_id: getValue("record_id") || null,
        is_new_client: getValue("is_new_client") === "true",
        reminder_kind: getValue("reminder_kind") || null
      };

      button.disabled = true;
      setStatus("Считаем preview...", "");
      try {
        const response = await fetch("/scheduler/dry-run-preview", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        renderResult(data);
        if (!response.ok) {
          setStatus("Не удалось построить preview. Проверьте данные.", "error");
        } else if (data.blocked_by_guard) {
          setStatus("Preview построен, но отправка была бы заблокирована safety guard'ами.", "error");
        } else {
          setStatus("Preview построен безопасно. Реальных отправок нет.", "success");
        }
      } catch (error) {
        setStatus("Не удалось связаться с сервером.", "error");
      } finally {
        button.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


class SchedulerToggleRequest(BaseModel):
    enabled: bool


class SchedulerToggleResponse(BaseModel):
    success: bool = True
    automation_enabled: bool


class SchedulerRunNowResponse(BaseModel):
    success: bool = True
    message: str = "Retention job triggered"


class SchedulerStagingStatusResponse(BaseModel):
    foundation_enabled: bool
    staging_mode: bool
    active_execution_enabled: bool
    background_loop_enabled: bool
    max_records_per_cycle: int
    only_test_recipients: bool
    test_recipients_configured: bool
    test_recipient_count: int
    dry_run_required: bool
    flowsell_dry_run: bool
    dry_run_enforced: bool
    safety_guards: tuple[str, ...]


class SchedulerDryRunPreviewRequest(BaseModel):
    flow_type: str
    service_name: str
    client_phone: str | None = None
    record_id: str | None = None
    is_new_client: bool = False
    reminder_kind: str | None = None


class DelayRulePreviewResponse(BaseModel):
    delay_type: str
    delay_value: int
    description: str


class SchedulerDryRunPreviewResponse(BaseModel):
    dry_run: bool
    would_send: bool
    blocked_by_guard: bool
    matched_flow: str | None
    matched_category: str | None
    matched_event: str | None
    template_id: str | None
    delay_rule: DelayRulePreviewResponse | None
    recipient_source: str
    selected_recipient: str | None
    reasons: list[str]
    guard_errors: list[str]
    safety_guards: list[str]
    provider_access: bool
    send_pipeline_called: bool
    background_execution: bool


@router.get("/staging-status", response_model=SchedulerStagingStatusResponse)
async def scheduler_staging_status() -> SchedulerStagingStatusResponse:
    """Read-only staging scheduler safety status. Does not start jobs or sends."""
    return SchedulerStagingStatusResponse(**get_scheduler_staging_status().to_dict())


@router.get("/planner-preview", response_class=HTMLResponse, include_in_schema=False)
async def scheduler_planner_preview_page() -> HTMLResponse:
    """Human-friendly UI for manual scheduler dry-run planning."""
    return HTMLResponse(PLANNER_PREVIEW_HTML)


@router.post("/dry-run-preview", response_model=SchedulerDryRunPreviewResponse)
async def scheduler_dry_run_preview(
    body: SchedulerDryRunPreviewRequest,
) -> SchedulerDryRunPreviewResponse:
    """Simulate one future scheduler decision. Does not render, send, or enqueue."""
    plan = build_scheduler_dry_run_plan(
        PlannerInput(
            flow_type=body.flow_type,  # type: ignore[arg-type]
            service_name=body.service_name,
            client_phone=body.client_phone,
            record_id=body.record_id,
            is_new_client=body.is_new_client,
            reminder_kind=body.reminder_kind,  # type: ignore[arg-type]
        ),
    )
    return SchedulerDryRunPreviewResponse(**plan.to_dict())


@router.post("/toggle", response_model=SchedulerToggleResponse)
async def toggle_scheduler(body: SchedulerToggleRequest) -> SchedulerToggleResponse:
    scheduler_setup.set_automation_enabled(body.enabled)
    return SchedulerToggleResponse(automation_enabled=body.enabled)


@router.post("/run-now", response_model=SchedulerRunNowResponse)
async def run_scheduler_now() -> SchedulerRunNowResponse:
    await scheduler_setup.run_retention_job_now()
    return SchedulerRunNowResponse()
