"""Управление retention automation scheduler."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.scheduler.dry_run_planner import PlannerInput, build_scheduler_dry_run_plan
from app.scheduler import setup as scheduler_setup
from app.scheduler.staging_execution import (
    StagingExecutionInput,
    StagingRealSendInput,
    build_staging_execution_preview,
    build_staging_provider_diagnostics,
    execute_staging_real_send_test,
)
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


STAGING_EXECUTION_PREVIEW_HTML = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Staging-проверка исполнения</title>
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
    main { width: min(1040px, calc(100% - 28px)); margin: 28px auto; }
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
    .badges { display: flex; gap: 10px; flex-wrap: wrap; margin: 18px 0; }
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
    label { display: grid; gap: 7px; font-weight: 650; color: #263246; }
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
    .help { color: var(--muted); font-size: 13px; font-weight: 500; }
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
    .status { min-height: 24px; font-weight: 750; }
    .status.error { color: var(--danger); }
    .status.success { color: var(--success); }
    .result { margin-top: 22px; display: none; border-top: 1px solid var(--border); padding-top: 20px; }
    .result.visible { display: block; }
    .summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 14px 0; }
    .metric, .section {
      border: 1px solid var(--border);
      border-radius: 15px;
      padding: 13px;
      background: #fbfcff;
    }
    .metric span { display: block; color: var(--muted); font-size: 12px; margin-bottom: 5px; }
    .sections { display: grid; gap: 12px; }
    .message {
      white-space: pre-wrap;
      max-height: 360px;
      overflow: auto;
      color: #263246;
    }
    .empty { color: var(--muted); }
    ul { margin: 8px 0 0; padding-left: 20px; }
    @media (max-width: 760px) {
      main { width: min(100% - 20px, 1040px); margin: 10px auto; }
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
      <h1>Staging-проверка исполнения</h1>
      <p>Ручная проверка одной записи: выбор сценария, подготовка текста сообщения и сбор данных отправки без отправки клиенту.</p>

      <div class="badges">
        <div class="badge">Только staging проверка</div>
        <div class="badge">Реальных отправок нет</div>
        <div class="badge">Провайдер отключён</div>
      </div>

      <div class="notice">
        Страница не запускает планировщик, фоновые задачи, очереди, повторы или провайдер. Проверка выполняется только по кнопке и только для одного тестового получателя.
      </div>

      <form id="executionForm">
        <label>
          Тип проверки
          <select id="flow_type" name="flow_type" required>
            <option value="review">Отзыв после визита</option>
            <option value="reminder">Напоминание о визите</option>
          </select>
        </label>
        <label>
          Услуга
          <input id="service_name" name="service_name" value="Стрижка женская" required />
          <span class="help">Например: стрижка, окрашивание, брови, уход, макияж, укладка.</span>
        </label>
        <label>
          Номер клиента
          <input id="client_phone" name="client_phone" inputmode="tel" placeholder="79991234567" />
          <span class="help">Используется как входные данные. Фактический получатель берётся из TEST_RECIPIENTS.</span>
        </label>
        <label>
          Клиент новый?
          <select id="is_new_client" name="is_new_client">
            <option value="false">Нет</option>
            <option value="true">Да</option>
          </select>
        </label>
        <label>
          ID записи
          <input id="record_id" name="record_id" value="demo-record-1" />
        </label>
        <label>
          Имя клиента для текста
          <input id="client_name" name="client_name" value="Анна" />
        </label>
        <label>
          Дата визита
          <input id="appointment_date" name="appointment_date" value="20.05.2026" />
        </label>
        <label>
          Время визита
          <input id="appointment_time" name="appointment_time" value="12:00" />
        </label>
        <label>
          Мастер
          <input id="master_name" name="master_name" value="Мария" />
        </label>
        <label>
          Ссылка для шаблона
          <input id="booking_link" name="booking_link" value="https://example.com/booking-preview" />
        </label>
        <div class="actions">
          <button id="submitButton" type="submit">Запустить staging-проверку</button>
          <div id="status" class="status" aria-live="polite"></div>
        </div>
      </form>

      <section id="result" class="result">
        <h2>Результат staging-проверки</h2>
        <div class="summary">
          <div class="metric"><span>Найденный сценарий</span><strong id="matchedEvent">-</strong></div>
          <div class="metric"><span>Категория</span><strong id="matchedCategory">-</strong></div>
          <div class="metric"><span>ID шаблона</span><strong id="templateId">-</strong></div>
          <div class="metric"><span>Использованный получатель</span><strong id="recipientUsed">-</strong></div>
          <div class="metric"><span>Провайдер заблокирован</span><strong id="providerBlocked">-</strong></div>
          <div class="metric"><span>Режим без отправки подтверждён</span><strong id="dryRunConfirmed">-</strong></div>
          <div class="metric"><span>Нормализованный chat_id</span><strong id="normalizedChatId">-</strong></div>
          <div class="metric"><span>Было бы готово к отправке</span><strong id="wouldBeSent">-</strong></div>
          <div class="metric"><span>Финальная остановка</span><strong id="finalStopStage">-</strong></div>
        </div>
        <div class="sections">
          <div class="section">
            <h2>Таймлайн исполнения</h2>
            <div id="timeline"></div>
          </div>
          <div class="section">
            <h2>Симулированные данные WhatsApp</h2>
            <div id="simulatedPayload"></div>
          </div>
          <div class="section">
            <h2>Предпросмотр текста сообщения</h2>
            <div id="renderedText" class="message empty">Сообщение ещё не сформировано.</div>
          </div>
          <div class="section">
            <h2>Выполненные шаги проверки</h2>
            <div id="steps"></div>
          </div>
          <div class="section">
            <h2>Активные защитные ограничения</h2>
            <div id="guards"></div>
          </div>
          <div class="section">
            <h2>Проверка данных отправки</h2>
            <div id="payloadChecks"></div>
          </div>
        </div>
      </section>
    </section>
  </main>

  <script>
    const form = document.getElementById("executionForm");
    const button = document.getElementById("submitButton");
    const statusNode = document.getElementById("status");
    const resultNode = document.getElementById("result");
    const yesNo = (value) => value ? "Да" : "Нет";
    const getValue = (id) => document.getElementById(id).value.trim();

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
      "max 1 record per cycle": "В staging-проверке разрешена максимум 1 запись",
      "TEST_RECIPIENTS only": "Используются только тестовые получатели",
      "FLOWSELL_DRY_RUN required": "Обязателен режим без реальной отправки",
      "no queues/workers/retry loops": "Очереди, воркеры и повторные попытки не используются",
      "controlled send adapter remains the only send path": "Ручной адаптер отправки остаётся единственным путём отправки"
    };
    const stepLabels = {
      manual_endpoint_invoked: "Ручная точка входа вызвана",
      single_record_guard: "Проверка ограничена одной записью",
      planner_selection: "Планировщик выбрал сценарий",
      category_matching: "Категория услуги определена",
      template_selection: "Шаблон выбран",
      payload_preparation: "Данные для шаблона подготовлены",
      template_rendering: "Текст сообщения сформирован",
      send_payload_build: "Данные отправки собраны в режиме без отправки",
      provider_blocked: "Провайдер заблокирован",
      blocked_before_payload_build: "Проверка остановлена до сборки данных отправки"
    };
    const timelineLabels = {
      scenario_matched: "1. Сценарий найден",
      scenario_not_matched: "1. Сценарий не найден",
      template_selected: "2. Шаблон выбран",
      template_not_selected: "2. Шаблон не выбран",
      text_rendered: "3. Текст собран",
      payload_prepared: "4. Данные отправки подготовлены",
      checks_passed: "5. Проверки пройдены",
      checks_failed: "5. Проверки не пройдены",
      send_blocked_by_dry_run: "6. Отправка заблокирована режимом без отправки",
      blocked_before_payload_build: "Проверка остановлена до подготовки данных отправки"
    };
    const stopStageLabels = {
      dry_run_provider_block: "Режим без отправки остановил перед провайдером",
      blocked_before_payload_build: "Остановлено до подготовки данных отправки"
    };
    const providerBlockReasonLabels = {
      flowsell_dry_run_enabled: "Включён FLOWSELL_DRY_RUN, вызов провайдера пропущен",
      safety_guard_before_provider: "Защитное ограничение остановило проверку до этапа провайдера",
      not_reached: "Этап провайдера не достигнут"
    };
    const statusLabels = {
      rendered: "Текст собран",
      render_failed: "Текст не собран",
      not_rendered: "Текст не собирался",
      valid: "Проверки пройдены",
      invalid: "Есть ошибки проверки",
      not_validated: "Проверка не выполнялась"
    };

    const setStatus = (message, kind = "") => {
      statusNode.textContent = message;
      statusNode.className = `status ${kind}`;
    };
    const labelFor = (labels, value) => labels[value] || value || "-";
    const renderList = (items, labels = {}, emptyText = "нет") => {
      if (!items || items.length === 0) return `<span class="empty">${emptyText}</span>`;
      return `<ul>${items.map((item) => `<li>${labelFor(labels, item)}</li>`).join("")}</ul>`;
    };

    const renderResult = (data) => {
      document.getElementById("matchedEvent").textContent = labelFor(eventLabels, data.matched_event);
      document.getElementById("matchedCategory").textContent = labelFor(categoryLabels, data.matched_category);
      document.getElementById("templateId").textContent = data.template_id || "-";
      document.getElementById("recipientUsed").textContent = data.recipient_used || "не выбран";
      document.getElementById("providerBlocked").textContent = yesNo(data.provider_blocked);
      document.getElementById("dryRunConfirmed").textContent = yesNo(data.dry_run_confirmed);
      document.getElementById("normalizedChatId").textContent = data.normalized_chat_id || "-";
      document.getElementById("wouldBeSent").textContent = yesNo(data.would_be_sent);
      document.getElementById("finalStopStage").textContent = labelFor(stopStageLabels, data.final_dry_run_stop_stage);

      const renderedText = document.getElementById("renderedText");
      renderedText.textContent = data.rendered_text_preview || "Сообщение не сформировано.";
      renderedText.className = data.rendered_text_preview ? "message" : "message empty";

      const simulatedPayload = data.simulated_whatsapp_payload || {};
      document.getElementById("timeline").innerHTML = renderList(data.execution_timeline, timelineLabels);
      document.getElementById("simulatedPayload").innerHTML = [
        `<div><strong>Провайдер:</strong> ${simulatedPayload.provider || "не выбран"}</div>`,
        `<div><strong>Канал:</strong> ${simulatedPayload.channel || "не выбран"}</div>`,
        `<div><strong>Chat ID:</strong> ${simulatedPayload.chat_id || "не сформирован"}</div>`,
        `<div><strong>Шаблон:</strong> ${data.template_used || data.template_id || "-"}</div>`,
        `<div><strong>Статус текста:</strong> ${labelFor(statusLabels, data.render_status)}</div>`,
        `<div><strong>Статус проверки данных:</strong> ${labelFor(statusLabels, data.payload_validation_status)}</div>`,
        `<div><strong>Причина блокировки провайдера:</strong> ${labelFor(providerBlockReasonLabels, data.provider_block_reason)}</div>`
      ].join("");
      document.getElementById("steps").innerHTML = renderList(data.execution_steps_completed, stepLabels);
      document.getElementById("guards").innerHTML = renderList(data.safety_guards, safetyGuardLabels);
      document.getElementById("payloadChecks").innerHTML = [
        `<div><strong>Доступ к провайдеру:</strong> ${data.provider_access ? "разрешён" : "отключён"}</div>`,
        `<div><strong>Адаптер отправки вызывался:</strong> ${yesNo(data.send_adapter_called)}</div>`,
        `<div><strong>Контур отправки вызывался:</strong> ${yesNo(data.send_pipeline_called)}</div>`,
        `<div><strong>Фоновое выполнение запускалось:</strong> ${yesNo(data.background_execution)}</div>`,
        `<div><strong>Ошибки защитных ограничений:</strong>${renderList(data.guard_errors, {}, "нет")}</div>`,
        `<div><strong>Ошибки данных отправки:</strong>${renderList(data.validation_errors, {}, "нет")}</div>`,
        `<div><strong>Предупреждения:</strong>${renderList(data.validation_warnings, {}, "нет")}</div>`
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
        client_name: getValue("client_name") || "Клиент",
        appointment_date: getValue("appointment_date") || "дата визита",
        appointment_time: getValue("appointment_time") || "время визита",
        master_name: getValue("master_name") || "мастер",
        booking_link: getValue("booking_link") || "https://example.com/booking-preview"
      };

      button.disabled = true;
      setStatus("Готовим staging-проверку...", "");
      try {
        const response = await fetch("/scheduler/staging-execute-preview", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        renderResult(data);
        if (!response.ok) {
          setStatus("Не удалось выполнить staging-проверку. Проверьте данные.", "error");
        } else if (!data.dry_run_confirmed || !data.provider_blocked) {
          setStatus("Проверка остановлена защитными ограничениями. Реальных отправок нет.", "error");
        } else {
          setStatus("Staging-проверка готова. Реальных отправок нет.", "success");
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


STAGING_SEND_TEST_HTML = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Реальная staging-отправка</title>
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
      --badge: #fff1f2;
      --badge-border: #fecdd3;
      --warning: #fff7ed;
      --warning-border: #fed7aa;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: radial-gradient(circle at top left, #ffe4e6, transparent 34%), var(--bg);
      color: var(--text);
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }
    main { width: min(1040px, calc(100% - 28px)); margin: 28px auto; }
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
    .badges { display: flex; gap: 10px; flex-wrap: wrap; margin: 18px 0; }
    .badge {
      border: 1px solid var(--badge-border);
      border-radius: 999px;
      background: var(--badge);
      color: #9f1239;
      font-weight: 850;
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
    form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 20px; }
    label { display: grid; gap: 7px; font-weight: 650; color: #263246; }
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
    input:focus, select:focus { outline: 3px solid rgba(37, 99, 235, 0.15); border-color: var(--primary); }
    .help { color: var(--muted); font-size: 13px; font-weight: 500; }
    .confirm {
      grid-column: 1 / -1;
      display: flex;
      align-items: center;
      gap: 10px;
      border: 1px solid var(--warning-border);
      background: var(--warning);
      border-radius: 15px;
      padding: 12px 14px;
    }
    .confirm input { width: auto; min-height: auto; }
    .actions { grid-column: 1 / -1; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-top: 4px; }
    button {
      border: 0;
      border-radius: 13px;
      padding: 13px 20px;
      background: #b91c1c;
      color: #fff;
      cursor: pointer;
      font: inherit;
      font-weight: 800;
      min-height: 48px;
    }
    button:disabled { opacity: 0.65; cursor: wait; }
    .status { min-height: 24px; font-weight: 750; }
    .status.error { color: var(--danger); }
    .status.success { color: var(--success); }
    .result { margin-top: 22px; display: none; border-top: 1px solid var(--border); padding-top: 20px; }
    .result.visible { display: block; }
    .summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 14px 0; }
    .metric, .section { border: 1px solid var(--border); border-radius: 15px; padding: 13px; background: #fbfcff; }
    .metric span { display: block; color: var(--muted); font-size: 12px; margin-bottom: 5px; }
    .sections { display: grid; gap: 12px; }
    .message { white-space: pre-wrap; max-height: 320px; overflow: auto; color: #263246; }
    .empty { color: var(--muted); }
    ul { margin: 8px 0 0; padding-left: 20px; }
    @media (max-width: 760px) {
      main { width: min(100% - 20px, 1040px); margin: 10px auto; }
      .card { padding: 18px; border-radius: 18px; }
      form, .summary { grid-template-columns: 1fr; }
      button { width: 100%; }
    }
  </style>
</head>
<body>
  <main>
    <section class="card">
      <h1>Реальная staging-отправка</h1>
      <p>Одна ручная контролируемая WhatsApp отправка только на первый тестовый номер.</p>

      <div class="badges">
        <div class="badge">Реальная тестовая отправка</div>
        <div class="badge">Только тестовый номер</div>
        <div class="badge">Automation отключена</div>
        <div class="badge">Отправляется только одно сообщение</div>
      </div>

      <div class="notice">
        Перед отправкой сервер проверяет явное подтверждение, режим реальной отправки и тестовый номер. Планировщик, фоновые задачи, очереди и массовые отправки не запускаются.
      </div>

      <form id="sendForm">
        <label>
          Тип проверки
          <select id="flow_type" required>
            <option value="review">Отзыв после визита</option>
            <option value="reminder">Напоминание о визите</option>
          </select>
        </label>
        <label>
          Услуга
          <input id="service_name" value="Стрижка женская" required />
        </label>
        <label>
          Номер клиента в записи
          <input id="client_phone" inputmode="tel" placeholder="79991234567" />
          <span class="help">Не используется как получатель. Отправка идёт только на первый тестовый номер.</span>
        </label>
        <label>
          Клиент новый?
          <select id="is_new_client">
            <option value="false">Нет</option>
            <option value="true">Да</option>
          </select>
        </label>
        <label>
          ID записи
          <input id="record_id" value="demo-record-1" />
        </label>
        <label>
          Имя клиента для текста
          <input id="client_name" value="Анна" />
        </label>
        <label>
          Дата визита
          <input id="appointment_date" value="20.05.2026" />
        </label>
        <label>
          Время визита
          <input id="appointment_time" value="12:00" />
        </label>
        <label>
          Мастер
          <input id="master_name" value="Мария" />
        </label>
        <label>
          Ссылка для шаблона
          <input id="booking_link" value="https://example.com/booking-preview" />
        </label>
        <label class="confirm">
          <input id="confirm_real_send" type="checkbox" />
          Я понимаю, что это реальная тестовая WhatsApp отправка на первый тестовый номер
        </label>
        <div class="actions">
          <button id="submitButton" type="submit">Отправить один тестовый WhatsApp</button>
          <div id="status" class="status" aria-live="polite"></div>
        </div>
      </form>

      <section id="result" class="result">
        <h2>Результат отправки</h2>
        <div class="summary">
          <div class="metric"><span>Статус отправки</span><strong id="sendStatus">-</strong></div>
          <div class="metric"><span>ID сообщения</span><strong id="messageId">-</strong></div>
          <div class="metric"><span>Получатель</span><strong id="recipient">-</strong></div>
          <div class="metric"><span>Сценарий</span><strong id="matchedEvent">-</strong></div>
          <div class="metric"><span>Шаблон</span><strong id="templateId">-</strong></div>
          <div class="metric"><span>ID чата</span><strong id="chatId">-</strong></div>
          <div class="metric"><span>Принято провайдером</span><strong id="providerAccepted">-</strong></div>
          <div class="metric"><span>Статус доставки</span><strong id="deliveryStatus">-</strong></div>
          <div class="metric"><span>Сессия WhatsApp</span><strong id="sessionState">-</strong></div>
        </div>
        <div class="sections">
          <div class="section">
            <h2>Текст сообщения</h2>
            <div id="renderedText" class="message empty">Сообщение ещё не сформировано.</div>
          </div>
          <div class="section">
            <h2>Таймлайн выполнения</h2>
            <div id="timeline"></div>
          </div>
          <div class="section">
            <h2>Проверки безопасности</h2>
            <div id="safetyChecks"></div>
          </div>
          <div class="section">
            <h2>Ответ провайдера</h2>
            <div id="providerResponse" class="empty">Ответ провайдера ещё не получен.</div>
          </div>
          <div class="section">
            <h2>Диагностика провайдера</h2>
            <div id="providerDiagnostics"></div>
          </div>
          <div class="section">
            <h2>Ошибки и предупреждения</h2>
            <div id="issues"></div>
          </div>
        </div>
      </section>
    </section>
  </main>

  <script>
    const form = document.getElementById("sendForm");
    const button = document.getElementById("submitButton");
    const statusNode = document.getElementById("status");
    const resultNode = document.getElementById("result");
    const getValue = (id) => document.getElementById(id).value.trim();
    const yesNo = (value) => value ? "Да" : "Нет";

    const eventLabels = {
      reminder_24h: "Напоминание за 24 часа",
      reminder_2h: "Напоминание за 2 часа",
      review_new_client_60m: "Отзыв новому клиенту",
      review_haircut_3d: "Отзыв после стрижки",
      review_coloring_3d: "Отзыв после окрашивания",
      review_brows_7d: "Отзыв после услуги по бровям",
      review_care_7d: "Отзыв после ухода",
      review_makeup_7d: "Отзыв после макияжа",
      review_styling_7d: "Отзыв после укладки"
    };
    const timelineLabels = {
      manual_endpoint_invoked: "Ручная точка входа вызвана",
      single_message_guard: "Ограничение: одно сообщение",
      planner_selection: "Планировщик выбрал сценарий",
      category_matching: "Категория определена",
      template_selection: "Шаблон выбран",
      template_rendering: "Текст собран",
      payload_validation: "Данные отправки проверены",
      send_adapter_execution: "Адаптер отправки выполнен один раз",
      provider_response_received: "Получен ответ провайдера",
      adapter_result_received: "Получен результат адаптера",
      blocked_before_send_adapter: "Остановлено до вызова адаптера отправки"
    };
    const safetyLabels = {
      "manual trigger only": "Только ручной запуск",
      "single message execution only": "Только одно сообщение",
      "TEST_RECIPIENTS[0] recipient only": "Получатель только первый тестовый номер",
      "FLOWSELL_DRY_RUN=false required": "Требуется FLOWSELL_DRY_RUN=false",
      "no scheduler/background execution": "Scheduler и фоновые задачи не запускаются",
      "no queues/workers/retries": "Очереди, воркеры и повторы не используются"
    };
    const sessionLabels = {
      authorized: "Авторизована",
      qr_login_required: "Нужно повторно отсканировать QR",
      qr_error: "Ошибка QR/session",
      qr_status_unavailable: "Статус session недоступен",
      not_configured: "FlowSell credentials не настроены",
      not_checked: "Не проверялась"
    };
    const recipientWhatsappLabels = {
      exists: "WhatsApp найден",
      not_found_or_unavailable: "WhatsApp не найден или проверка недоступна",
      not_checked: "Не проверялся"
    };
    const connectionLabels = {
      settings_available: "Instance отвечает",
      settings_unavailable: "Instance settings недоступны",
      not_configured: "FlowSell credentials не настроены",
      not_checked: "Не проверялось"
    };
    const failureReasonLabels = {
      "WhatsApp session requires QR login": "Сессия WhatsApp требует повторного входа по QR",
      "TEST_RECIPIENTS[0] may not have WhatsApp or checkWhatsapp is unavailable": "У тестового номера может не быть WhatsApp или проверка номера недоступна",
      "Provider accepted message, but delivery status lookup is unavailable": "Провайдер принял сообщение, но статус доставки пока недоступен"
    };
    const failureReasonText = (reason) => {
      if (!reason) return "не выявлена";
      if (failureReasonLabels[reason]) return failureReasonLabels[reason];
      if (reason.startsWith("Provider delivery status: ")) {
        return `Статус доставки у провайдера: ${reason.replace("Provider delivery status: ", "")}`;
      }
      if (reason.startsWith("Provider accepted message, delivery is still ")) {
        return `Провайдер принял сообщение, доставка пока в статусе ${reason.replace("Provider accepted message, delivery is still ", "")}`;
      }
      if (reason.startsWith("WhatsApp session state: ")) {
        return `Состояние WhatsApp session: ${reason.replace("WhatsApp session state: ", "")}`;
      }
      return reason;
    };

    const setStatus = (message, kind = "") => {
      statusNode.textContent = message;
      statusNode.className = `status ${kind}`;
    };
    const labelFor = (labels, value) => labels[value] || value || "-";
    const renderList = (items, labels = {}, emptyText = "нет") => {
      if (!items || items.length === 0) return `<span class="empty">${emptyText}</span>`;
      return `<ul>${items.map((item) => `<li>${labelFor(labels, item)}</li>`).join("")}</ul>`;
    };

    const renderResult = (data) => {
      document.getElementById("sendStatus").textContent = data.blocked
        ? "Заблокировано"
        : (data.sent ? "Отправлено" : "Не отправлено");
      document.getElementById("messageId").textContent = data.message_id || "-";
      document.getElementById("recipient").textContent = data.recipient_used || "не выбран";
      document.getElementById("matchedEvent").textContent = labelFor(eventLabels, data.matched_event);
      document.getElementById("templateId").textContent = data.template_id || "-";
      document.getElementById("chatId").textContent = data.chat_id || "-";
      const diagnostics = data.provider_diagnostics || {};
      document.getElementById("providerAccepted").textContent = yesNo(diagnostics.provider_accepted);
      document.getElementById("deliveryStatus").textContent = diagnostics.delivery_status || "не проверен";
      document.getElementById("sessionState").textContent = labelFor(sessionLabels, diagnostics.whatsapp_session_state);

      const renderedText = document.getElementById("renderedText");
      renderedText.textContent = data.rendered_text || "Сообщение не сформировано.";
      renderedText.className = data.rendered_text ? "message" : "message empty";

      document.getElementById("timeline").innerHTML = renderList(data.execution_timeline, timelineLabels);
      document.getElementById("safetyChecks").innerHTML = renderList(data.safety_checks, safetyLabels);
      document.getElementById("providerResponse").textContent = data.provider_response_preview || "Ответ провайдера отсутствует или отправка заблокирована.";
      document.getElementById("providerResponse").className = data.provider_response_preview ? "" : "empty";
      document.getElementById("providerDiagnostics").innerHTML = [
        `<div><strong>Принято провайдером:</strong> ${yesNo(diagnostics.provider_accepted)}</div>`,
        `<div><strong>Состояние instance:</strong> ${labelFor(connectionLabels, diagnostics.connection_state)}</div>`,
        `<div><strong>Сессия WhatsApp:</strong> ${labelFor(sessionLabels, diagnostics.whatsapp_session_state)}</div>`,
        `<div><strong>Нужен повторный QR вход:</strong> ${diagnostics.qr_login_required === null || diagnostics.qr_login_required === undefined ? "неизвестно" : yesNo(diagnostics.qr_login_required)}</div>`,
        `<div><strong>WhatsApp на тестовом номере:</strong> ${labelFor(recipientWhatsappLabels, diagnostics.test_recipient_whatsapp)}</div>`,
        `<div><strong>Статус доставки:</strong> ${diagnostics.delivery_status || "недоступен"}</div>`,
        `<div><strong>Состояние доставки у провайдера:</strong> ${diagnostics.provider_delivery_state || "неизвестно"}</div>`,
        `<div><strong>Возможная причина:</strong> ${failureReasonText(diagnostics.possible_failure_reason)}</div>`,
        `<div><strong>Account WID:</strong> ${diagnostics.account_wid || "-"}</div>`,
        `<div><strong>Webhook настроен:</strong> ${diagnostics.webhook_configured === null || diagnostics.webhook_configured === undefined ? "неизвестно" : yesNo(diagnostics.webhook_configured)}</div>`,
        `<div><strong>Ошибки диагностики:</strong>${renderList(diagnostics.diagnostics_errors, {}, "нет")}</div>`
      ].join("");
      document.getElementById("issues").innerHTML = [
        `<div><strong>Ошибки защитных проверок:</strong>${renderList(data.guard_errors, {}, "нет")}</div>`,
        `<div><strong>Ошибки данных отправки:</strong>${renderList(data.validation_errors, {}, "нет")}</div>`,
        `<div><strong>Предупреждения:</strong>${renderList(data.warnings, {}, "нет")}</div>`,
        `<div><strong>Адаптер отправки вызывался:</strong> ${yesNo(data.send_adapter_called)}</div>`,
        `<div><strong>Фоновое выполнение запускалось:</strong> ${yesNo(data.background_execution)}</div>`,
        `<div><strong>Массовая отправка запускалась:</strong> ${yesNo(data.bulk_execution)}</div>`
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
        client_name: getValue("client_name") || "Клиент",
        appointment_date: getValue("appointment_date") || "дата визита",
        appointment_time: getValue("appointment_time") || "время визита",
        master_name: getValue("master_name") || "мастер",
        booking_link: getValue("booking_link") || "https://example.com/booking-preview",
        confirm_real_send: document.getElementById("confirm_real_send").checked
      };

      button.disabled = true;
      setStatus("Выполняем контролируемую staging-отправку...", "");
      try {
        const response = await fetch("/scheduler/staging-send-test", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        renderResult(data);
        if (!response.ok || data.blocked) {
          setStatus("Отправка заблокирована защитными проверками.", "error");
        } else if (data.sent) {
          setStatus("Одно тестовое WhatsApp сообщение отправлено.", "success");
        } else {
          setStatus("Адаптер отправки выполнен, но сообщение не отправлено. Проверьте предупреждения.", "error");
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


class SchedulerStagingExecutePreviewRequest(SchedulerDryRunPreviewRequest):
    client_name: str = "Клиент"
    appointment_date: str = "дата визита"
    appointment_time: str = "время визита"
    master_name: str = "мастер"
    booking_link: str = "https://example.com/booking-preview"
    channel: str = "sms"


class SchedulerStagingSendTestRequest(SchedulerStagingExecutePreviewRequest):
    confirm_real_send: bool = False


class SchedulerProviderDiagnosticsRequest(BaseModel):
    message_id: str


class SchedulerStagingSendPayloadPreviewResponse(BaseModel):
    event: str
    template: str
    phone: str
    channel: str
    delivery_channel: str
    chat_id: str | None
    valid: bool
    validation_errors: list[str]
    validation_warnings: list[str]
    missing_placeholders: list[str]


class SchedulerSimulatedWhatsAppPayloadResponse(BaseModel):
    chat_id: str | None
    message: str
    channel: str
    provider: str


class SchedulerStagingExecutePreviewResponse(BaseModel):
    dry_run: bool
    dry_run_confirmed: bool
    provider_blocked: bool
    provider_access: bool
    send_adapter_called: bool
    send_pipeline_called: bool
    background_execution: bool
    matched_flow: str | None
    matched_category: str | None
    matched_event: str | None
    template_id: str | None
    rendered_text_preview: str | None
    recipient_used: str | None
    record_id: str | None
    execution_steps_completed: list[str]
    guard_errors: list[str]
    safety_guards: list[str]
    validation_errors: list[str]
    validation_warnings: list[str]
    simulated_whatsapp_payload: SchedulerSimulatedWhatsAppPayloadResponse | None
    normalized_chat_id: str | None
    template_used: str | None
    render_status: str
    payload_validation_status: str
    would_be_sent: bool
    provider_block_reason: str
    final_dry_run_stop_stage: str
    execution_timeline: list[str]
    send_payload_preview: SchedulerStagingSendPayloadPreviewResponse | None


class SchedulerProviderDiagnosticsResponse(BaseModel):
    provider_accepted: bool
    connection_state: str
    whatsapp_session_state: str
    qr_login_required: bool | None
    test_recipient_whatsapp: str
    delivery_status: str
    delivery_status_available: bool
    provider_delivery_state: str
    possible_failure_reason: str | None
    diagnostics_errors: list[str]
    account_wid: str | int | None = None
    webhook_configured: bool | None = None


class SchedulerStagingSendTestResponse(BaseModel):
    manual_trigger_only: bool
    single_message_execution: bool
    confirm_real_send: bool
    blocked: bool
    sent: bool
    dry_run: bool
    matched_category: str | None
    matched_event: str | None
    template_id: str | None
    adapter_event: str | None
    rendered_text: str | None
    recipient_used: str | None
    chat_id: str | None
    message_id: str | None
    provider: str
    provider_response_preview: str | None
    execution_timeline: list[str]
    safety_checks: list[str]
    guard_errors: list[str]
    validation_errors: list[str]
    warnings: list[str]
    provider_diagnostics: SchedulerProviderDiagnosticsResponse | None
    send_adapter_called: bool
    provider_access: bool
    background_execution: bool
    bulk_execution: bool


@router.get("/staging-status", response_model=SchedulerStagingStatusResponse)
async def scheduler_staging_status() -> SchedulerStagingStatusResponse:
    """Read-only staging scheduler safety status. Does not start jobs or sends."""
    return SchedulerStagingStatusResponse(**get_scheduler_staging_status().to_dict())


@router.get("/planner-preview", response_class=HTMLResponse, include_in_schema=False)
async def scheduler_planner_preview_page() -> HTMLResponse:
    """Human-friendly UI for manual scheduler dry-run planning."""
    return HTMLResponse(PLANNER_PREVIEW_HTML)


@router.get("/staging-execution-preview", response_class=HTMLResponse, include_in_schema=False)
async def scheduler_staging_execution_preview_page() -> HTMLResponse:
    """Human-friendly UI for one-record staging execution preview."""
    return HTMLResponse(STAGING_EXECUTION_PREVIEW_HTML)


@router.get("/staging-send-test", response_class=HTMLResponse, include_in_schema=False)
async def scheduler_staging_send_test_page() -> HTMLResponse:
    """Human-friendly UI for one explicit staging-only test send."""
    return HTMLResponse(STAGING_SEND_TEST_HTML)


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


@router.post("/staging-execute-preview", response_model=SchedulerStagingExecutePreviewResponse)
async def scheduler_staging_execute_preview(
    body: SchedulerStagingExecutePreviewRequest,
) -> SchedulerStagingExecutePreviewResponse:
    """Manual one-record dry-run execution preview. Never calls provider or send adapter."""
    result = build_staging_execution_preview(
        StagingExecutionInput(
            flow_type=body.flow_type,
            service_name=body.service_name,
            client_phone=body.client_phone,
            record_id=body.record_id,
            is_new_client=body.is_new_client,
            reminder_kind=body.reminder_kind,
            client_name=body.client_name,
            appointment_date=body.appointment_date,
            appointment_time=body.appointment_time,
            master_name=body.master_name,
            booking_link=body.booking_link,
            channel=body.channel,
        ),
    )
    return SchedulerStagingExecutePreviewResponse(**result.to_dict())


@router.post("/staging-send-test", response_model=SchedulerStagingSendTestResponse)
async def scheduler_staging_send_test(
    body: SchedulerStagingSendTestRequest,
) -> SchedulerStagingSendTestResponse:
    """Explicit staging-only single real send test. Never used by scheduler execution."""
    result = await execute_staging_real_send_test(
        StagingRealSendInput(
            flow_type=body.flow_type,
            service_name=body.service_name,
            client_phone=body.client_phone,
            record_id=body.record_id,
            is_new_client=body.is_new_client,
            reminder_kind=body.reminder_kind,
            client_name=body.client_name,
            appointment_date=body.appointment_date,
            appointment_time=body.appointment_time,
            master_name=body.master_name,
            booking_link=body.booking_link,
            channel=body.channel,
            confirm_real_send=body.confirm_real_send,
        ),
    )
    return SchedulerStagingSendTestResponse(**result.to_dict())


@router.post("/staging-provider-diagnostics", response_model=SchedulerProviderDiagnosticsResponse)
async def scheduler_staging_provider_diagnostics(
    body: SchedulerProviderDiagnosticsRequest,
) -> SchedulerProviderDiagnosticsResponse:
    """Read-only provider diagnostics for a previous staging message id."""
    result = await build_staging_provider_diagnostics(message_id=body.message_id)
    return SchedulerProviderDiagnosticsResponse(**result.to_dict())


@router.post("/toggle", response_model=SchedulerToggleResponse)
async def toggle_scheduler(body: SchedulerToggleRequest) -> SchedulerToggleResponse:
    scheduler_setup.set_automation_enabled(body.enabled)
    return SchedulerToggleResponse(automation_enabled=body.enabled)


@router.post("/run-now", response_model=SchedulerRunNowResponse)
async def run_scheduler_now() -> SchedulerRunNowResponse:
    await scheduler_setup.run_retention_job_now()
    return SchedulerRunNowResponse()
