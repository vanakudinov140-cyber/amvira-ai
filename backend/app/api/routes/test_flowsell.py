"""Тестовая отправка через FlowSell API (не для production automation)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.integrations.flowsell.client import FlowsellClient
from app.integrations.flowsell.exceptions import FlowsellNotConfiguredError
from app.integrations.flowsell.orchestration import FlowSellSendOrchestrator
from app.integrations.flowsell.send_adapter import FlowSellSendAdapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["test"])

FLOWSELL_DEMO_HTML = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Тест WhatsApp-сообщений</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7fb;
      --card: #ffffff;
      --text: #172033;
      --muted: #667085;
      --border: #dfe5ef;
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --danger: #b91c1c;
      --success: #047857;
      --soft: #eef4ff;
      --soft-border: #c7d7fe;
      --warning-bg: #fff7ed;
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
    .header {
      display: grid;
      gap: 8px;
      margin-bottom: 18px;
    }
    h1 { margin: 0; font-size: clamp(24px, 4vw, 34px); letter-spacing: -0.03em; }
    h2 { margin: 22px 0 10px; font-size: 18px; }
    p { margin: 0; color: var(--muted); }
    .notice {
      margin: 18px 0;
      padding: 14px 16px;
      border-radius: 16px;
      background: var(--warning-bg);
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
    .help {
      color: var(--muted);
      font-size: 13px;
      font-weight: 500;
    }
    .full { grid-column: 1 / -1; }
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
    .scenario-description {
      grid-column: 1 / -1;
      padding: 14px 16px;
      border-radius: 16px;
      background: var(--soft);
      border: 1px solid var(--soft-border);
      color: #1e3a8a;
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
    button:hover { background: var(--primary-dark); }
    button:disabled { opacity: 0.65; cursor: wait; }
    .status {
      min-height: 24px;
      font-weight: 750;
    }
    .status.success { color: var(--success); }
    .status.error { color: var(--danger); }
    .result {
      margin-top: 22px;
      display: none;
      border-top: 1px solid var(--border);
      padding-top: 20px;
    }
    .result.visible { display: block; }
    .summary {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 14px 0;
    }
    .metric {
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
    .message-preview, .details-list {
      border: 1px solid var(--border);
      border-radius: 16px;
      background: #fbfcff;
      padding: 16px;
    }
    .message-preview {
      white-space: pre-wrap;
      color: #263246;
    }
    .details-list {
      display: grid;
      gap: 8px;
      margin-top: 12px;
    }
    .empty { color: var(--muted); }
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
      <div class="header">
        <h1>Тест WhatsApp-сообщений</h1>
        <p>Страница для ручной проверки одного сообщения перед запуском. Массовых отправок и автоматизации здесь нет.</p>
      </div>

      <div class="notice">
        Быстрое отключение отправок: установите <strong>FLOWSELL_DRY_RUN=true</strong> и <strong>TEST_MODE=true</strong>.
      </div>

      <form id="sendForm">
        <label>
          Номер телефона
          <input id="phone" name="phone" inputmode="tel" autocomplete="tel" placeholder="79504744246" required />
          <span class="help">Укажите номер получателя WhatsApp в международном формате.</span>
        </label>
        <label>
          Тип сообщения
          <select id="event" name="event" required>
            <option value="appointment_created">Подтверждение записи</option>
            <option value="appointment_rescheduled">Перенос записи</option>
            <option value="appointment_cancelled">Отмена записи</option>
            <option value="reminder_24h">Напоминание за день</option>
            <option value="reminder_2h">Напоминание за 2 часа</option>
            <option value="review_new_client_60m">Запрос отзыва новому клиенту</option>
          </select>
        </label>

        <div id="scenarioDescription" class="scenario-description"></div>

        <label>
          Имя клиента
          <input id="client_name" name="client_name" value="Анна" required />
        </label>
        <label>
          Услуга
          <input id="service_name" name="service_name" value="Окрашивание" required />
        </label>
        <label>
          Дата
          <input id="appointment_date" name="appointment_date" value="22 мая" required />
        </label>
        <label>
          Время
          <input id="appointment_time" name="appointment_time" value="14:30" required />
        </label>
        <label>
          Мастер
          <input id="master_name" name="master_name" value="Мария" />
        </label>
        <label>
          Ссылка на запись
          <input id="booking_link" name="booking_link" placeholder="https://..." required />
        </label>
        <div class="actions">
          <button id="submitButton" type="submit">Отправить тест</button>
          <div id="status" class="status" aria-live="polite"></div>
        </div>
      </form>

      <section id="result" class="result">
        <h2>Результат отправки</h2>
        <div class="summary">
          <div class="metric"><span>Отправлено</span><strong id="sentValue">-</strong></div>
          <div class="metric"><span>Тестовый режим</span><strong id="dryRunValue">-</strong></div>
          <div class="metric"><span>Номер сообщения</span><strong id="messageIdValue">-</strong></div>
          <div class="metric"><span>Сервис отправки</span><strong id="providerValue">-</strong></div>
        </div>

        <h2>Текст сообщения</h2>
        <div id="messagePreview" class="message-preview"></div>

        <h2>Проверка</h2>
        <div id="checks" class="details-list"></div>
      </section>
    </section>
  </main>

  <script>
    const scenarios = {
      appointment_created: "Клиент получает подтверждение новой записи с датой, временем, мастером и ссылкой на изменение записи.",
      appointment_rescheduled: "Клиент получает уведомление, что запись перенесена на новое время.",
      appointment_cancelled: "Клиент получает подтверждение отмены записи и ссылку для выбора нового времени.",
      reminder_24h: "Клиент получает мягкое напоминание за день до визита.",
      reminder_2h: "Клиент получает короткое напоминание за 2 часа до визита.",
      review_new_client_60m: "Сообщение с просьбой оставить отзыв после первого визита клиента."
    };

    const form = document.getElementById("sendForm");
    const button = document.getElementById("submitButton");
    const statusNode = document.getElementById("status");
    const resultNode = document.getElementById("result");
    const checksNode = document.getElementById("checks");
    const messagePreview = document.getElementById("messagePreview");
    const scenarioSelect = document.getElementById("event");
    const scenarioDescription = document.getElementById("scenarioDescription");

    const setStatus = (message, kind = "") => {
      statusNode.textContent = message;
      statusNode.className = `status ${kind}`;
    };

    const getValue = (id) => document.getElementById(id).value.trim();
    const yesNo = (value) => value ? "Да" : "Нет";

    const updateScenarioDescription = () => {
      scenarioDescription.textContent = scenarios[scenarioSelect.value] || "";
    };

    const validateForm = () => {
      const phoneDigits = getValue("phone").replace(/\\D/g, "");
      if (phoneDigits.length < 10) {
        return "Укажите номер телефона минимум из 10 цифр.";
      }
      if (!getValue("booking_link").startsWith("http")) {
        return "Укажите ссылку на запись, начинающуюся с http или https.";
      }
      return "";
    };

    const renderList = (title, items) => {
      if (!items || items.length === 0) {
        return `<div><strong>${title}:</strong> <span class="empty">нет</span></div>`;
      }
      return `<div><strong>${title}:</strong><ul>${items.map((item) => `<li>${item}</li>`).join("")}</ul></div>`;
    };

    const providerName = (provider) => provider ? "WhatsApp" : "-";

    const renderResult = (data) => {
      document.getElementById("sentValue").textContent = yesNo(data.sent);
      document.getElementById("dryRunValue").textContent = yesNo(data.dry_run);
      document.getElementById("messageIdValue").textContent = data.message_id || "-";
      document.getElementById("providerValue").textContent = providerName(data.provider);
      messagePreview.textContent = data.rendered_text || "Текст сообщения не сформирован.";

      checksNode.innerHTML = [
        renderList("Ошибки проверки", data.validation_errors),
        renderList("Предупреждения", data.warnings),
        data.provider_response_preview
          ? `<div><strong>Ответ сервиса отправки:</strong> сообщение обработано.</div>`
          : `<div><strong>Ответ сервиса отправки:</strong> <span class="empty">нет данных</span></div>`
      ].join("");

      resultNode.classList.add("visible");
    };

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const validationError = validateForm();
      if (validationError) {
        setStatus(validationError, "error");
        return;
      }

      const payload = {
        phone: getValue("phone"),
        event: getValue("event"),
        channel: "sms",
        values: {
          client_name: getValue("client_name"),
          service_name: getValue("service_name"),
          appointment_date: getValue("appointment_date"),
          appointment_time: getValue("appointment_time"),
          master_name: getValue("master_name"),
          booking_link: getValue("booking_link")
        }
      };

      button.disabled = true;
      setStatus("Отправляем тестовое сообщение...", "");
      try {
        const response = await fetch("/test/send-real", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        renderResult(data);
        if (!response.ok) {
          setStatus("Не удалось выполнить запрос. Проверьте данные и попробуйте ещё раз.", "error");
        } else if (data.sent) {
          setStatus("Сообщение успешно отправлено.", "success");
        } else if (data.dry_run) {
          setStatus("Тестовый режим: сообщение подготовлено, но не отправлено клиенту.", "success");
        } else {
          setStatus("Сообщение не отправлено. Посмотрите ошибки проверки и предупреждения ниже.", "error");
        }
      } catch (error) {
        setStatus("Не удалось связаться с сервером. Проверьте подключение и попробуйте ещё раз.", "error");
      } finally {
        button.disabled = false;
      }
    });

    scenarioSelect.addEventListener("change", updateScenarioDescription);
    updateScenarioDescription();
  </script>
</body>
</html>
"""


class FlowsellTestSendBody(BaseModel):
    phone: str = Field(..., min_length=10, description="Номер в международном формате")
    message: str = Field(..., min_length=1, max_length=4096)
    channel: str = Field(default="sms", description="Retention channel label (sms/telegram)")


class FlowsellTestSendResponse(BaseModel):
    ok: bool
    detail: str
    id_message: str | None = None


class FlowSellTemplateRenderBody(BaseModel):
    event: str = Field(..., min_length=1)
    service_type: str | None = None
    values: dict[str, str | int | float | None] = Field(default_factory=dict)


class FlowSellSendPreviewBody(FlowSellTemplateRenderBody):
    phone: str = Field(..., min_length=1)
    channel: str = Field(default="sms", description="Retention channel label")


class FlowSellPayloadPreviewResponse(BaseModel):
    event: str
    phone: str
    template: str
    rendered_text: str
    missing_placeholders: list[str]
    dry_run: bool
    service_type: str | None = None
    channel: str
    delivery_channel: str
    chat_id: str | None = None
    validation_errors: list[str]
    validation_warnings: list[str]
    valid: bool


class FlowSellControlledSendResponse(BaseModel):
    dry_run: bool
    sent: bool
    provider: str
    event: str
    template: str
    rendered_text: str
    phone: str
    chat_id: str | None = None
    message_id: str | None = None
    service_type: str | None = None
    channel: str
    validation_errors: list[str]
    warnings: list[str]
    provider_response_preview: str | None = None


@router.get("/flowsell-demo", response_class=HTMLResponse, include_in_schema=False)
async def flowsell_demo_page() -> HTMLResponse:
    """Lightweight internal UI for manual single-message FlowSell tests."""
    return HTMLResponse(FLOWSELL_DEMO_HTML)


@router.post("/render-template", response_model=FlowSellPayloadPreviewResponse)
async def flowsell_render_template(
    body: FlowSellTemplateRenderBody,
) -> FlowSellPayloadPreviewResponse:
    """Dry-run render only. No FlowSell API calls."""
    preview = FlowSellSendOrchestrator().render_template(
        event=body.event,
        service_type=body.service_type,
        values=body.values,
    )
    return FlowSellPayloadPreviewResponse(**preview.to_dict())


@router.post("/send-preview", response_model=FlowSellPayloadPreviewResponse)
async def flowsell_send_preview(body: FlowSellSendPreviewBody) -> FlowSellPayloadPreviewResponse:
    """Dry-run send preview. Builds payload and validation report; does not send."""
    preview = FlowSellSendOrchestrator().build_send_preview(
        event=body.event,
        phone=body.phone,
        service_type=body.service_type,
        channel=body.channel,
        values=body.values,
    )
    return FlowSellPayloadPreviewResponse(**preview.to_dict())


@router.post("/send-real", response_model=FlowSellControlledSendResponse)
async def flowsell_send_real(body: FlowSellSendPreviewBody) -> FlowSellControlledSendResponse:
    """
    Controlled single-message send adapter.

    Safe by default: FLOWSELL_DRY_RUN=true returns preview-like result and does
    not call FlowSell. Real provider call requires FLOWSELL_DRY_RUN=false,
    TEST_MODE=false, credentials, and valid payload.
    """
    result = await FlowSellSendAdapter().send_event(
        event=body.event,
        phone=body.phone,
        service_type=body.service_type,
        channel=body.channel,
        values=body.values,
    )
    return FlowSellControlledSendResponse(**result.to_dict())


@router.post("/flowsell-send", response_model=FlowsellTestSendResponse)
async def flowsell_test_send(body: FlowsellTestSendBody) -> FlowsellTestSendResponse:
    """
  Прямой test send в FlowSell WhatsApp API.

  Требует FLOWSELL_INSTANCE_ID + FLOWSELL_API_KEY.
  При TEST_MODE=true используйте отдельный тестовый instance или временно TEST_MODE=false.
  """
    settings = get_settings()
    if settings.TEST_MODE:
        raise HTTPException(
            status_code=400,
            detail="Отключите TEST_MODE или используйте scripts/test_flowsell_send.py с TEST_MODE=false",
        )
    if not settings.flowsell_configured:
        raise HTTPException(
            status_code=503,
            detail="FlowSell не настроен: FLOWSELL_INSTANCE_ID и FLOWSELL_API_KEY",
        )

    try:
        async with FlowsellClient(settings) as client:
            result = await client.send_message(
                phone=body.phone,
                text=body.message,
                channel=body.channel,
            )
    except FlowsellNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    logger.info(
        "test flowsell-send phone=%s ok=%s id_message=%s",
        body.phone[:4] + "***",
        result.ok,
        result.id_message,
    )
    return FlowsellTestSendResponse(
        ok=result.ok,
        detail=result.detail,
        id_message=result.id_message,
    )
