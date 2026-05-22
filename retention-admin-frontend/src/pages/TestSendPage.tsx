import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { AlertTriangle, Check, Eye, MessageCircle, RotateCcw, SendHorizonal, ShieldCheck, Smartphone } from "lucide-react";
import { apiClient, getErrorMessage } from "@/api/client";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { DEMO_MODE } from "@/constants";
import { cn } from "@/lib/utils";

type ScenarioId = "reminder_24h" | "reminder_2h" | "appointment_rescheduled" | "appointment_cancelled";

type Scenario = {
  id: ScenarioId;
  title: string;
  kind: "reminder" | "lifecycle";
  reminderKind?: "24h" | "2h";
};

type CandidatePlan = {
  record_id: number;
  client_name: string;
  client_phone: string | null;
  service_name: string;
  appointment_datetime: string;
};

type ExecutionPreviewResponse = {
  plans: CandidatePlan[];
};

type DryRunPreviewResponse = {
  selected_recipient: string | null;
};

type StagingPreviewResponse = {
  template_id: string | null;
  template_used: string | null;
  rendered_text_preview: string | null;
  validation_errors: string[];
};

type RenderTemplateResponse = {
  template: string;
  rendered_text: string;
  validation_errors: string[];
};

type DemoSendStatusResponse = {
  demo_mode: boolean;
  send_available: boolean;
  cooldown_seconds: number;
  allowed_recipients: string[];
  provider_connected: boolean;
  max_test_send: number;
};

type DemoSendResponse = {
  dry_run: boolean;
  sent: boolean;
  status: string;
  provider: string;
  phone: string;
  channel: string;
  message_id: string | null;
  validation_errors: string[];
};

type PreviewDetails = {
  clientName: string;
  serviceName: string;
  appointmentDate: string;
  appointmentTime: string;
  masterName: string;
  bookingLink: string;
  template: string;
  text: string;
  errors: string[];
};

const SCENARIOS: Scenario[] = [
  { id: "reminder_24h", title: "Напоминание за 24 часа", kind: "reminder", reminderKind: "24h" },
  { id: "reminder_2h", title: "Напоминание за 2 часа", kind: "reminder", reminderKind: "2h" },
  { id: "appointment_rescheduled", title: "Перенос записи", kind: "lifecycle" },
  { id: "appointment_cancelled", title: "Отмена записи", kind: "lifecycle" },
];

const DEFAULT_RECORD_ID = "98";
const DEFAULT_BOOKING_LINK = "https://n1057414.yclients.com";
const EMPTY_RESULT_TEXT = "Результат появится после подтверждённого теста";
const TEST_SEND_COOLDOWN_SECONDS = 10;
const DEMO_VALUES = {
  clientName: "Анна",
  serviceName: "Окрашивание",
  appointmentDate: "Завтра",
  appointmentTime: "14:30",
  masterName: "Мария",
  bookingLink: "демо",
};

function renderDemoText(scenarioId: ScenarioId) {
  const base = `${DEMO_VALUES.clientName}, добрый день ☀️

Это бьюти-пространство «ВНЕ РАМОК».`;

  if (scenarioId === "reminder_2h") {
    return `${base} Напоминаем, что через 2 часа у вас запланирована процедура «${DEMO_VALUES.serviceName}» 🤩

📅 Дата: ${DEMO_VALUES.appointmentDate}
⏰ Время: ${DEMO_VALUES.appointmentTime}
💆‍♀️ Услуга: ${DEMO_VALUES.serviceName}
👩‍💼 Мастер: ${DEMO_VALUES.masterName}
🔗 Детали: ${DEMO_VALUES.bookingLink}

До встречи! Если что-то изменилось, просто напишите нам.`;
  }

  if (scenarioId === "appointment_rescheduled") {
    return `${base} Уведомляем вас о переносе записи.

📅 Дата: ${DEMO_VALUES.appointmentDate}
⏰ Время: ${DEMO_VALUES.appointmentTime}
💆‍♀️ Услуга: ${DEMO_VALUES.serviceName}
🔗 Детали: ${DEMO_VALUES.bookingLink}

Если потребуется скорректировать время, мы рядом.`;
  }

  if (scenarioId === "appointment_cancelled") {
    return `${base} Уведомляем вас об отмене записи.

📅 Дата: ${DEMO_VALUES.appointmentDate}
⏰ Время: ${DEMO_VALUES.appointmentTime}
💆‍♀️ Услуга: ${DEMO_VALUES.serviceName}
🔗 Новая запись: ${DEMO_VALUES.bookingLink}

Если захотите записаться снова, мы всегда на связи.`;
  }

  return `${base} Напоминаем, что через 24 часа у вас запланирована процедура «${DEMO_VALUES.serviceName}» 🤩

Пожалуйста, подтвердите свою запись перед визитом.

📅 Дата: ${DEMO_VALUES.appointmentDate}
⏰ Время: ${DEMO_VALUES.appointmentTime}
💆‍♀️ Услуга: ${DEMO_VALUES.serviceName}
👩‍💼 Мастер: ${DEMO_VALUES.masterName}
🔗 Подтверждение: ${DEMO_VALUES.bookingLink}

Ждём вашего подтверждения или сообщения 🌸`;
}

function formatDateTime(value: string): { date: string; time: string } {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return { date: "дата записи", time: "время записи" };
  }
  return {
    date: date.toLocaleDateString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    }),
    time: date.toLocaleTimeString("ru-RU", {
      hour: "2-digit",
      minute: "2-digit",
    }),
  };
}

function fallbackValues(): Omit<PreviewDetails, "template" | "text" | "errors"> {
  return {
    clientName: "Клиент",
    serviceName: "Услуга из записи",
    appointmentDate: "дата записи",
    appointmentTime: "время записи",
    masterName: "мастер",
    bookingLink: DEFAULT_BOOKING_LINK,
  };
}

export function TestSendPage() {
  const location = useLocation();
  const demoSafeMode = DEMO_MODE || location.pathname.startsWith("/demo");
  const [scenarioId, setScenarioId] = useState<ScenarioId>("reminder_24h");
  const [recordId, setRecordId] = useState(DEFAULT_RECORD_ID);
  const [recipient, setRecipient] = useState("");
  const [preview, setPreview] = useState<PreviewDetails | null>(null);
  const [status, setStatus] = useState("Сообщение ещё не отправлено");
  const [resultText] = useState(EMPTY_RESULT_TEXT);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [demoPhone, setDemoPhone] = useState("");
  const [demoConfirmed, setDemoConfirmed] = useState(false);
  const [demoStatus, setDemoStatus] = useState("Отправка недоступна");
  const [demoSending, setDemoSending] = useState(false);
  const [sendConfirmOpen, setSendConfirmOpen] = useState(false);
  const [finalSendConfirmed, setFinalSendConfirmed] = useState(false);
  const [sendResultStatus, setSendResultStatus] = useState("—");
  const [sendResultChannel, setSendResultChannel] = useState("—");
  const [sendResultPhone, setSendResultPhone] = useState("—");
  const [sendResultMessageId, setSendResultMessageId] = useState("—");
  const [sendResultTime, setSendResultTime] = useState("—");
  const [lastTestSendTime, setLastTestSendTime] = useState<number | null>(null);
  const [cooldownLeft, setCooldownLeft] = useState(0);
  const [phonePreviewOpen, setPhonePreviewOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedScenario = useMemo(
    () => SCENARIOS.find((scenario) => scenario.id === scenarioId) ?? SCENARIOS[0],
    [scenarioId],
  );
  const activeStep = preview ? 3 : isLoading ? 2 : 1;
  const singleDemoPhone = demoPhone.trim().length > 0 && !/[;,]/.test(demoPhone);
  const messageAlreadyReceived = sendResultMessageId !== "—";
  const sendButtonDisabled = !demoConfirmed || !singleDemoPhone || demoSending || cooldownLeft > 0;

  useEffect(() => {
    let cancelled = false;

    async function loadRecipient() {
      if (demoSafeMode) {
        setRecipient("");
        return;
      }
      try {
        const { data } = await apiClient.post<DryRunPreviewResponse>("/scheduler/dry-run-preview", {
          flow_type: "reminder",
          service_name: "Тестовая услуга",
          record_id: recordId,
          reminder_kind: "24h",
        });
        if (!cancelled && data.selected_recipient) {
          setRecipient(data.selected_recipient);
        }
      } catch {
        if (!cancelled) {
          setRecipient("");
        }
      }
    }

    loadRecipient();
    return () => {
      cancelled = true;
    };
  }, [demoSafeMode, recordId]);

  useEffect(() => {
    let cancelled = false;

    async function loadDemoMode() {
      try {
        const { data } = await apiClient.get<DemoSendStatusResponse>("/test/demo-send/status");
        if (!cancelled) {
          setDemoMode(data.send_available);
          setDemoStatus(data.send_available ? "Реальная тестовая отправка включена" : "Отправка недоступна");
        }
      } catch {
        if (!cancelled) {
          setDemoMode(false);
          setDemoStatus("Отправка недоступна");
        }
      }
    }

    loadDemoMode();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!lastTestSendTime) return;
    const sentAt = lastTestSendTime;

    function updateCooldown() {
      const elapsed = Math.floor((Date.now() - sentAt) / 1000);
      setCooldownLeft(Math.max(TEST_SEND_COOLDOWN_SECONDS - elapsed, 0));
    }

    updateCooldown();
    const timer = window.setInterval(updateCooldown, 1000);
    return () => window.clearInterval(timer);
  }, [lastTestSendTime]);

  async function loadRecordValues(): Promise<Omit<PreviewDetails, "template" | "text" | "errors">> {
    const base = fallbackValues();
    if (demoSafeMode) {
      return {
        clientName: DEMO_VALUES.clientName,
        serviceName: DEMO_VALUES.serviceName,
        appointmentDate: DEMO_VALUES.appointmentDate,
        appointmentTime: DEMO_VALUES.appointmentTime,
        masterName: DEMO_VALUES.masterName,
        bookingLink: DEMO_VALUES.bookingLink,
      };
    }
    const numericRecordId = Number(recordId);
    if (!Number.isFinite(numericRecordId)) {
      return base;
    }

    const { data } = await apiClient.post<ExecutionPreviewResponse>("/scheduler/execution-preview", {
      flow_type: "reminder",
      max_candidates: 50,
      reminder_horizon_hours: 168,
    });
    const record = data.plans.find((candidate) => candidate.record_id === numericRecordId);
    if (!record) {
      return base;
    }

    const { date, time } = formatDateTime(record.appointment_datetime);
    return {
      clientName: record.client_name || base.clientName,
      serviceName: record.service_name || base.serviceName,
      appointmentDate: date,
      appointmentTime: time,
      masterName: "мастер",
      bookingLink: DEFAULT_BOOKING_LINK,
    };
  }

  async function buildPreview() {
    setIsLoading(true);
    setError(null);
    setStatus("Готовим предпросмотр");
    setIsConfirmed(false);

    try {
      const values = await loadRecordValues();
      if (demoSafeMode) {
        setPreview({
          ...values,
          template: selectedScenario.title,
          text: renderDemoText(selectedScenario.id),
          errors: [],
        });
      } else if (selectedScenario.kind === "reminder") {
        const { data } = await apiClient.post<StagingPreviewResponse>("/scheduler/staging-execute-preview", {
          flow_type: "reminder",
          service_name: values.serviceName,
          client_phone: recipient,
          record_id: recordId,
          reminder_kind: selectedScenario.reminderKind,
          client_name: values.clientName,
          appointment_date: values.appointmentDate,
          appointment_time: values.appointmentTime,
          master_name: values.masterName,
          booking_link: values.bookingLink,
          channel: "sms",
        });
        setPreview({
          ...values,
          template: data.template_id || data.template_used || "шаблон не выбран",
          text: data.rendered_text_preview || "",
          errors: data.validation_errors || [],
        });
      } else {
        const { data } = await apiClient.post<RenderTemplateResponse>("/test/render-template", {
          event: selectedScenario.id,
          service_type: null,
          values: {
            client_name: values.clientName,
            service_name: values.serviceName,
            appointment_date: values.appointmentDate,
            appointment_time: values.appointmentTime,
            master_name: values.masterName,
            booking_link: values.bookingLink,
          },
        });
        setPreview({
          ...values,
          template: data.template,
          text: data.rendered_text,
          errors: data.validation_errors || [],
        });
      }
      setStatus("Сообщение ещё не отправлено");
    } catch (caught) {
      setError(getErrorMessage(caught));
      setStatus("Предпросмотр не сформирован");
    } finally {
      setIsLoading(false);
    }
  }

  async function sendDemoMessage() {
    if (!demoMode || !demoConfirmed || !singleDemoPhone) return;
    setDemoSending(true);
    setDemoStatus("Выполняем тестовую отправку");
    try {
      const phone = demoPhone.replace(/\D+/g, "");
      const { data } = await apiClient.post<DemoSendResponse>("/test/send-real", {
        event: "reminder_24h",
        service_type: null,
        phone,
        channel: "sms",
        values: {
          client_name: DEMO_VALUES.clientName,
          service_name: DEMO_VALUES.serviceName,
          appointment_date: DEMO_VALUES.appointmentDate,
          appointment_time: DEMO_VALUES.appointmentTime,
          master_name: DEMO_VALUES.masterName,
          booking_link: DEMO_VALUES.bookingLink,
        },
      });
      const statusText = data.sent ? "✓ Сообщение отправлено" : "Отправка недоступна";
      setDemoStatus(statusText);
      setSendResultStatus(statusText);
      setSendResultChannel(data.channel || "—");
      setSendResultPhone(data.phone || phone);
      setSendResultMessageId(data.message_id || "—");
      setSendResultTime(new Date().toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }));
      if (data.sent) {
        setLastTestSendTime(Date.now());
      }
      setSendConfirmOpen(false);
      setFinalSendConfirmed(false);
    } catch (caught) {
      const statusText = getErrorMessage(caught) || "Отправка недоступна";
      setDemoStatus(statusText);
      setSendResultStatus(statusText);
      setSendResultChannel("—");
      setSendResultPhone(demoPhone.replace(/\D+/g, "") || "—");
      setSendResultMessageId("—");
      setSendResultTime(new Date().toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }));
    } finally {
      setDemoSending(false);
    }
  }

  function resetScenarioCheck() {
    setPreview(null);
    setIsConfirmed(false);
    setPhonePreviewOpen(false);
    setStatus("Сообщение ещё не отправлено");
    setError(null);
  }

  return (
    <main className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6">
      <section className="rounded-2xl border border-sky-500/30 bg-sky-500/10 p-5 text-sky-50">
        <div className="flex items-start gap-3">
          <ShieldCheck className="mt-1 h-5 w-5 text-sky-200" />
          <div>
            <h2 className="text-lg font-semibold">Тестовая среда</h2>
            <p className="mt-1 text-sm text-sky-100/80">
              {demoSafeMode
                ? "Здесь можно безопасно проверять сценарии без реальных данных. Реальная отправка доступна только на тестовые номера."
                : "Здесь можно безопасно проверять сценарии и отправлять тестовые сообщения."}
            </p>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-sm font-medium text-primary">Тестовая консоль</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight">Тестовая отправка сообщений</h2>
            <p className="mt-2 text-muted-foreground">Проверка сценариев без массовых запусков</p>
          </div>
          <Badge variant="outline" className="w-fit border-emerald-500/50 px-3 py-1 text-emerald-200">
            Только предпросмотр
          </Badge>
        </div>
        <div className="mt-5 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-50">
          <p className="font-semibold">{demoSafeMode ? "Демонстрационная среда" : "Рабочая среда"}</p>
          <p className="mt-1 text-amber-100/80">
            {demoSafeMode
              ? "API, база данных и provider не подключены."
              : "Реальные действия защищены дополнительными ограничениями."}
          </p>
        </div>
        <div className="mt-6 flex flex-col gap-3 rounded-xl border border-border bg-background/60 p-3 sm:flex-row sm:items-center sm:justify-between">
          <Step active={activeStep === 1} done={activeStep > 1} number="①" label="Выберите сценарий" />
          <span className="hidden text-muted-foreground sm:block">→</span>
          <Step active={activeStep === 2} done={activeStep > 2} number="②" label="Проверьте сообщение" />
          <span className="hidden text-muted-foreground sm:block">→</span>
          <Step active={activeStep === 3} done={false} number="③" label="Подтвердите тест" />
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Сценарий</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {SCENARIOS.map((scenario) => (
                <label
                  key={scenario.id}
                  className={cn(
                    "flex cursor-pointer items-center gap-3 rounded-lg border p-3 text-sm transition-colors",
                    scenarioId === scenario.id
                      ? "border-primary bg-primary/10 text-foreground"
                      : "border-border bg-background hover:bg-muted/50",
                  )}
                >
                  <input
                    type="radio"
                    name="scenario"
                    value={scenario.id}
                    checked={scenarioId === scenario.id}
                    onChange={() => setScenarioId(scenario.id)}
                    className="h-4 w-4 accent-primary"
                  />
                  <span>{scenario.title}</span>
                </label>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Источник данных</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <label className="flex items-center gap-3 rounded-lg border border-primary bg-primary/10 p-3 text-sm">
                <input type="radio" checked readOnly className="h-4 w-4 accent-primary" />
                <span>{demoSafeMode ? "Демо-данные" : "Реальная запись"}</span>
              </label>
              {demoSafeMode ? (
                <p className="text-sm text-muted-foreground">
                  Используются только встроенные демонстрационные значения, без API и базы данных.
                </p>
              ) : (
                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="record-id">
                    Номер записи
                  </label>
                  <Input
                    id="record-id"
                    value={recordId}
                    onChange={(event) => setRecordId(event.target.value)}
                    placeholder="Например: 98"
                  />
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Канал</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg border border-border bg-muted/40 p-4">
                <div className="flex items-center gap-2 text-lg font-semibold">
                  <MessageCircle className="h-5 w-5 text-emerald-300" />
                  Ватсап
                </div>
                <p className="mt-1 text-sm text-muted-foreground">Другие каналы появятся позже</p>
              </div>
            </CardContent>
          </Card>

          {!demoSafeMode ? (
            <Card>
              <CardHeader>
                <CardTitle>Получатель</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <label className="text-sm font-medium" htmlFor="recipient-phone">
                  Телефон для теста
                </label>
                <Input
                  id="recipient-phone"
                  value={recipient}
                  onChange={(event) => setRecipient(event.target.value)}
                  placeholder="Будет подставлен тестовый номер"
                />
                <p className="text-sm text-muted-foreground">Разрешены только тестовые номера</p>
              </CardContent>
            </Card>
          ) : null}
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between gap-3">
              <CardTitle>Предпросмотр</CardTitle>
              <Button onClick={buildPreview} disabled={isLoading}>
                <Eye className="h-4 w-4" />
                {isLoading ? "Готовим" : "Показать сообщение"}
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {error ? <Alert variant="destructive">{error}</Alert> : null}
              {preview ? (
                <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4 text-emerald-50">
                  <p className="font-semibold">Сообщение успешно подготовлено</p>
                  <p className="mt-1 text-sm text-emerald-100/80">Текст готов к проверке перед запуском</p>
                </div>
              ) : null}
              <div className="grid gap-3 md:grid-cols-2">
                <Info label="Имя клиента" value={preview?.clientName} />
                <Info label="Услуга" value={preview?.serviceName} />
                <Info label="Дата" value={preview?.appointmentDate} />
                <Info label="Время" value={preview?.appointmentTime} />
                <Info label="Мастер" value={preview?.masterName} />
                <Info label="Ссылка" value={preview?.bookingLink} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="message-text">
                  Полный текст сообщения
                </label>
                <Textarea
                  id="message-text"
                  readOnly
                  value={preview?.text || ""}
                  placeholder="Нажмите «Показать сообщение», чтобы увидеть текст"
                  className="min-h-[360px] whitespace-pre-wrap"
                />
              </div>
              <div className="flex flex-col gap-2 rounded-lg border border-border bg-muted/40 p-4 text-sm">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{status}</Badge>
                  {preview?.template ? <span className="text-muted-foreground">Сценарий подготовлен</span> : null}
                </div>
                {preview?.errors.length ? (
                  <p className="text-red-200">Проверьте данные: {preview.errors.join(", ")}</p>
                ) : null}
              </div>
              {preview ? (
                <div className="flex flex-col gap-3 sm:flex-row">
                  <Button variant="secondary" onClick={() => setPhonePreviewOpen(true)}>
                    <Smartphone className="h-4 w-4" />
                    Показать как это будет выглядеть у клиента
                  </Button>
                  <Button variant="outline" onClick={resetScenarioCheck}>
                    <RotateCcw className="h-4 w-4" />
                    Проверить другой сценарий
                  </Button>
                </div>
              ) : null}
              <div className="grid gap-3 rounded-lg border border-border bg-background p-4 text-sm md:grid-cols-2">
                <div>
                  <p className="font-medium">Что проверяется:</p>
                  <ul className="mt-2 space-y-1 text-muted-foreground">
                    <li>✓ текст сообщения</li>
                    <li>✓ данные клиента</li>
                    <li>✓ ссылка</li>
                    <li>✓ сценарий</li>
                  </ul>
                </div>
                <div>
                  <p className="font-medium">Что сейчас НЕ выполняется:</p>
                  <ul className="mt-2 space-y-1 text-muted-foreground">
                    <li>— массовая отправка</li>
                    <li>— автоматическая работа</li>
                    <li>— отправка без подтверждения</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Отправка</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <div className="flex gap-3">
                  <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-300" />
                  <div>
                    <p className="font-medium">🛡️ Защитный режим включён</p>
                    <p className="mt-1 text-muted-foreground">
                      Массовые действия недоступны
                    </p>
                  </div>
                </div>
              </Alert>
              {preview ? (
                <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border bg-background p-4 text-sm">
                  <input
                    type="checkbox"
                    checked={isConfirmed}
                    onChange={(event) => setIsConfirmed(event.target.checked)}
                    className="mt-0.5 h-4 w-4 accent-primary"
                  />
                  <span>Я проверил сообщение и понимаю, что это только тест</span>
                </label>
              ) : null}
              <Button
                onClick={() => setSendConfirmOpen(true)}
                disabled={!demoMode || sendButtonDisabled}
                className="w-full"
              >
                <SendHorizonal className="h-4 w-4" />
                {messageAlreadyReceived ? "Проверить ещё раз" : "Отправить тест"}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Демонстрационная отправка</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-lg border border-border bg-background p-4 text-sm">
                <p className="font-medium">Демо-сообщение будет собрано без реальных записей.</p>
                <div className="mt-3 grid gap-2 text-muted-foreground md:grid-cols-2">
                  <span>Имя: {DEMO_VALUES.clientName}</span>
                  <span>Услуга: {DEMO_VALUES.serviceName}</span>
                  <span>Дата: {DEMO_VALUES.appointmentDate}</span>
                  <span>Время: {DEMO_VALUES.appointmentTime}</span>
                  <span>Мастер: {DEMO_VALUES.masterName}</span>
                  <span>Ссылка: {DEMO_VALUES.bookingLink}</span>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="demo-phone">
                  Ваш номер телефона
                </label>
                <Input
                  id="demo-phone"
                  value={demoPhone}
                  onChange={(event) => setDemoPhone(event.target.value)}
                  placeholder="Введите один номер"
                />
              </div>
              <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border bg-background p-4 text-sm">
                <input
                  type="checkbox"
                  checked={demoConfirmed}
                  onChange={(event) => setDemoConfirmed(event.target.checked)}
                  className="mt-0.5 h-4 w-4 accent-primary"
                />
                <span>Я понимаю, что это демонстрационный тест</span>
              </label>
              {demoMode ? (
                cooldownLeft > 0 ? (
                  <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4 text-sm text-emerald-50">
                    <p className="font-semibold">Тест уже выполнен</p>
                    <p className="mt-1 text-emerald-100/80">
                      Повторная проверка будет доступна через {formatCooldown(cooldownLeft)}
                    </p>
                  </div>
                ) : (
                  <Button
                    onClick={() => setSendConfirmOpen(true)}
                    disabled={sendButtonDisabled}
                    className="w-full"
                  >
                    <SendHorizonal className="h-4 w-4" />
                    {messageAlreadyReceived ? "Проверить ещё раз" : "Отправить тест"}
                  </Button>
                )
              ) : (
                <div className="rounded-xl border border-sky-500/30 bg-sky-500/10 p-4 text-sm text-sky-50">
                  <p className="font-semibold">Тестовая отправка выключена</p>
                  <p className="mt-1 text-sky-100/80">
                    Включите ALLOW_TEST_RECIPIENTS=true и задайте TEST_RECIPIENTS, чтобы отправлять только на тестовые номера.
                  </p>
                </div>
              )}
              <div className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
                {demoStatus}
              </div>
              <div className="rounded-lg border border-violet-500/30 bg-violet-500/10 p-4 text-sm text-violet-50">
                <p className="font-semibold">🧪 Можно выполнять повторные проверки</p>
                <p className="mt-1 text-violet-100/80">
                  Следующий тест через: {formatCooldown(cooldownLeft)}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Результат</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg border border-dashed border-border p-5 text-sm text-muted-foreground">
                {resultText}
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-5">
                <Info label="Статус" value={sendResultStatus} />
                <Info label="Канал" value={sendResultChannel} />
                <Info label="Номер" value={sendResultPhone} />
                <Info label="message_id" value={sendResultMessageId} />
                <Info label="Время" value={sendResultTime} />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Как проходит запуск</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="grid gap-3 text-sm md:grid-cols-4">
            <li className="rounded-lg border border-border bg-background p-4">
              <span className="font-semibold">Предпросмотр</span>
            </li>
            <li className="rounded-lg border border-border bg-background p-4">
              <span className="font-semibold">Тест</span>
            </li>
            <li className="rounded-lg border border-border bg-background p-4">
              <span className="font-semibold">Подтверждение</span>
            </li>
            <li className="rounded-lg border border-border bg-background p-4">
              <span className="font-semibold">{demoSafeMode ? "Проверка" : "Запуск"}</span>
            </li>
          </ol>
        </CardContent>
      </Card>
      <div className="flex items-center justify-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
        <ShieldCheck className="h-4 w-4" />
        🛡️ Защитный режим включён. Массовые действия недоступны
      </div>
      <Dialog
        open={phonePreviewOpen}
        onClose={() => setPhonePreviewOpen(false)}
        title="Как это будет выглядеть у клиента"
        className="max-w-md"
      >
        <div className="mx-auto max-w-[320px] rounded-[2rem] border border-border bg-zinc-950 p-3 shadow-2xl">
          <div className="rounded-[1.5rem] bg-[#0b141a] p-4 text-white">
            <div className="mb-4 flex items-center gap-3 border-b border-white/10 pb-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-600 font-semibold">
                ВР
              </div>
              <div>
                <p className="text-sm font-semibold">ВНЕ РАМОК</p>
                <p className="text-xs text-white/60">Имитация сообщения</p>
              </div>
            </div>
            <div className="rounded-2xl rounded-tl-sm bg-[#005c4b] p-3 text-sm leading-relaxed shadow">
              <pre className="whitespace-pre-wrap font-sans">{preview?.text || "Сообщение пока не подготовлено"}</pre>
            </div>
          </div>
        </div>
      </Dialog>
      <Dialog
        open={sendConfirmOpen}
        onClose={() => {
          setSendConfirmOpen(false);
          setFinalSendConfirmed(false);
        }}
        title="Подтвердите тестовую отправку"
        className="max-w-md"
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Будет отправлено одно настоящее сообщение на указанный тестовый номер.
          </p>
          <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border bg-background p-4 text-sm">
            <input
              type="checkbox"
              checked={finalSendConfirmed}
              onChange={(event) => setFinalSendConfirmed(event.target.checked)}
              className="mt-0.5 h-4 w-4 accent-primary"
            />
            <span>Я понимаю и подтверждаю тест</span>
          </label>
          <Button
            onClick={sendDemoMessage}
            disabled={!finalSendConfirmed || !singleDemoPhone || demoSending || cooldownLeft > 0}
            className="w-full"
          >
            <SendHorizonal className="h-4 w-4" />
            {demoSending ? "Отправляем" : "Отправить тест"}
          </Button>
        </div>
      </Dialog>
    </main>
  );
}

function Step({ active, done, number, label }: { active: boolean; done: boolean; number: string; label: string }) {
  return (
    <div
      className={cn(
        "flex flex-1 items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
        active && "bg-primary text-primary-foreground",
        !active && done && "bg-emerald-500/10 text-emerald-100",
        !active && !done && "text-muted-foreground",
      )}
    >
      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-background/20 font-semibold">
        {done ? <Check className="h-4 w-4" /> : number}
      </span>
      <span className="font-medium">{label}</span>
    </div>
  );
}

function formatCooldown(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="rounded-lg border border-border bg-background p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 min-h-5 text-sm font-medium">{value || "—"}</p>
    </div>
  );
}
