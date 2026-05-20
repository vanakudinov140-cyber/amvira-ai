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
      <p>Безопасная проверка: показывает, какой сценарий был бы выбран для одной записи. Сообщения не отправляются.</p>

      <div class="badges">
        <div class="badge">Только проверка</div>
        <div class="badge">Без реальных отправок</div>
        <div class="badge">Провайдер отключён</div>
      </div>

      <div class="notice">
        Эта страница не запускает расписание, фоновые задачи, очереди или отправки. Она только показывает безопасный расчёт для администратора.
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
          <span class="help">Используется только для проверки. Реальный получатель берётся из списка тестовых номеров.</span>
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
          <button id="submitButton" type="submit">Показать проверку</button>
          <div id="status" class="status" aria-live="polite"></div>
        </div>
      </form>

      <section id="result" class="result">
        <h2>Результат проверки</h2>
        <div class="summary">
          <div class="metric"><span>Тип сценария</span><strong id="matchedFlow">-</strong></div>
          <div class="metric"><span>Найденное событие</span><strong id="matchedEvent">-</strong></div>
          <div class="metric"><span>Категория услуги</span><strong id="matchedCategory">-</strong></div>
          <div class="metric"><span>Выбран шаблон</span><strong id="templateId">-</strong></div>
          <div class="metric"><span>Когда отправлялось бы</span><strong id="delayRule">-</strong></div>
          <div class="metric"><span>Режим проверки включён</span><strong id="dryRun">-</strong></div>
          <div class="metric"><span>Заблокировано защитой</span><strong id="blocked">-</strong></div>
          <div class="metric"><span>План допускает отправку</span><strong id="wouldSend">-</strong></div>
        </div>
        <h2>Почему выбран этот сценарий</h2>
        <div id="reasons" class="details"></div>
        <h2>Защитные ограничения</h2>
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
    const flowLabels = {
      review: "Отзыв после визита",
      reminder: "Напоминание о визите"
    };
    const categoryLabels = {
      reminder: "Напоминание",
      new_client: "Новый клиент",
      haircut: "Стрижка",
      coloring: "Окрашивание",
      brows: "Брови",
      care: "Уход",
      makeup: "Макияж",
      styling: "Укладка"
    };
    const eventLabels = {
      reminder_24h: "Напоминание за 24 часа до визита",
      reminder_2h: "Напоминание за 2 часа до визита",
      review_new_client_60m: "Запрос отзыва новому клиенту через 60 минут",
      review_haircut_3d: "Запрос отзыва после стрижки через 3 дня",
      review_coloring_3d: "Запрос отзыва после окрашивания через 3 дня",
      review_brows_7d: "Запрос отзыва после услуги по бровям через 7 дней",
      review_care_7d: "Запрос отзыва после ухода через 7 дней",
      review_makeup_7d: "Запрос отзыва после макияжа через 7 дней",
      review_styling_7d: "Запрос отзыва после укладки через 7 дней"
    };
    const safetyGuardLabels = {
      "no active scheduler execution": "Автоматический планировщик не запущен",
      "no background infinite loops": "Фоновые циклы не работают",
      "max 1 record per cycle": "В будущей проверке разрешена максимум 1 запись за цикл",
      "TEST_RECIPIENTS only": "Разрешены только тестовые получатели",
      "FLOWSELL_DRY_RUN required": "Обязателен режим без реальной отправки",
      "no queues/workers/retry loops": "Очереди, воркеры и повторные попытки не используются",
      "controlled send adapter remains the only send path": "Единственный путь отправки остаётся под ручным контролем"
    };
    const guardErrorLabels = {
      "no matching flow": "Подходящий сценарий не найден",
      "SCHEDULER_STAGING_MAX_RECORDS must be 1": "Лимит проверки должен быть ровно 1 запись",
      "FLOWSELL_DRY_RUN must be true for scheduler dry-run planner": "Для планировщика должен быть включён режим без реальной отправки",
      "TEST_RECIPIENTS must contain at least one phone": "Нужно указать хотя бы один тестовый номер"
    };

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

    const labelFor = (labels, value) => labels[value] || value || "-";

    const recipientSourceText = (source) => {
      if (source === "TEST_RECIPIENTS[0]") return "первый тестовый номер";
      if (source === "none") return "получатель не настроен";
      return source || "не указан";
    };

    const reasonText = (reason) => {
      if (reason === "manual reminder_kind=24h selected") return "Администратор выбрал напоминание за 24 часа.";
      if (reason === "manual reminder_kind=2h selected") return "Администратор выбрал напоминание за 2 часа.";
      if (reason === "is_new_client=true matched new client review flow") return "Клиент отмечен как новый, поэтому выбран запрос отзыва после первого визита.";
      if (reason === "service category was not matched") return "Не удалось определить категорию услуги. Сценарий отзыва не выбран.";
      if (reason.startsWith("service_name matched category=")) {
        const category = reason.replace("service_name matched category=", "");
        return `Услуга совпала с категорией: ${labelFor(categoryLabels, category)}.`;
      }
      if (reason.startsWith("no review event registered for category=")) {
        const category = reason.replace("no review event registered for category=", "");
        return `Для категории "${labelFor(categoryLabels, category)}" пока нет сценария отзыва.`;
      }
      return reason;
    };

    const translateItems = (items, labels) => (items || []).map((item) => labels[item] || reasonText(item));

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
      document.getElementById("matchedFlow").textContent = labelFor(flowLabels, data.matched_flow);
      document.getElementById("matchedEvent").textContent = labelFor(eventLabels, data.matched_event);
      document.getElementById("matchedCategory").textContent = labelFor(categoryLabels, data.matched_category);
      document.getElementById("templateId").textContent = data.template_id || "-";
      document.getElementById("delayRule").textContent = delayText(data.delay_rule);
      document.getElementById("dryRun").textContent = yesNo(data.dry_run);
      document.getElementById("blocked").textContent = yesNo(data.blocked_by_guard);
      document.getElementById("wouldSend").textContent = data.would_send
        ? "Да, если бы автоматика была включена"
        : "Нет";

      document.getElementById("reasons").innerHTML = [
        `<div><strong>Причины выбора:</strong>${renderList(translateItems(data.reasons, {}))}</div>`,
        `<div><strong>Получатель для проверки:</strong> ${data.selected_recipient || "не выбран"} (${recipientSourceText(data.recipient_source)})</div>`,
        `<div><strong>Реальная отправка:</strong> не выполняется, это только безопасная проверка.</div>`
      ].join("");

      document.getElementById("guards").innerHTML = [
        `<div><strong>Что остановило бы отправку:</strong>${renderList(translateItems(data.guard_errors, guardErrorLabels), "ничего")}</div>`,
        `<div><strong>Активные защитные ограничения:</strong>${renderList(translateItems(data.safety_guards, safetyGuardLabels))}</div>`,
        `<div><strong>Доступ к провайдеру отправки:</strong> ${data.provider_access ? "разрешён" : "отключён"}</div>`,
        `<div><strong>Контур отправки вызывался:</strong> ${yesNo(data.send_pipeline_called)}</div>`,
        `<div><strong>Фоновое выполнение запускалось:</strong> ${yesNo(data.background_execution)}</div>`
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
      setStatus("Готовим безопасную проверку...", "");
      try {
        const response = await fetch("/scheduler/dry-run-preview", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        renderResult(data);
        if (!response.ok) {
          setStatus("Не удалось подготовить проверку. Проверьте данные.", "error");
        } else if (data.blocked_by_guard) {
          setStatus("Проверка готова: защитные ограничения заблокировали бы отправку.", "error");
        } else {
          setStatus("Проверка готова. Реальных отправок нет.", "success");
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
