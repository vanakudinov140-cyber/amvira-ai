import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Clock3, Info, ShieldCheck } from "lucide-react";
import { apiClient, getErrorMessage } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Tone = "success" | "destructive" | "secondary" | "outline";
type OperationMode = "SAFE" | "MANUAL ONLY" | "AUTOMATION ENABLED" | "UNKNOWN";
type SystemStatus = "OK" | "DEGRADED" | "UNKNOWN";
type RiskStatus = "LOW" | "GUARDED" | "DEGRADED";
type SnapshotStatus = "Fresh" | "Stale";
type HealthLoadState = "loading" | "connected" | "unavailable";
type LiveLoadState = "loading" | "connected" | "unavailable";

interface HealthSliceState {
  api: HealthLoadState;
  db: HealthLoadState;
  apiLabel: string;
  dbLabel: string;
  loadedAt: number | null;
  error: string | null;
}

interface StagingStatusResponse {
  foundation_enabled?: boolean;
  staging_mode?: boolean;
  active_execution_enabled?: boolean;
  background_loop_enabled?: boolean;
  max_records_per_cycle?: number;
  only_test_recipients?: boolean;
  test_recipients_configured?: boolean;
  test_recipient_count?: number;
  dry_run_required?: boolean;
  flowsell_dry_run?: boolean;
  dry_run_enforced?: boolean;
  safety_guards?: string[];
}

interface StagingSliceState {
  state: LiveLoadState;
  data: typeof operationsFixture.staging | null;
  loadedAt: number | null;
  error: string | null;
}

interface DeliveryAdaptersStatusResponse {
  read_only?: boolean;
  adapter_foundation_only?: boolean;
  automation_enabled?: boolean;
  primary_channel?: string;
  fallback_chain?: string[];
  provider_access?: boolean;
  send_adapter_called?: boolean;
  safety_guards?: string[];
  adapters?: Array<{
    channel?: string;
    configured?: boolean;
    foundation_ready?: boolean;
    real_send_enabled?: boolean;
    health?: {
      state?: string;
      errors?: string[];
    };
  }>;
}

interface AdaptersSliceState {
  state: LiveLoadState;
  data: typeof operationsFixture.adapters | null;
  guards: string[];
  loadedAt: number | null;
  error: string | null;
}

interface SchedulerMonitoringStatusResponse {
  automation_enabled?: boolean;
  background_execution_enabled?: boolean;
  cron_execution_enabled?: boolean;
  queue_execution_enabled?: boolean;
  bulk_execution_enabled?: boolean;
  emergency_stop_active?: boolean;
  emergency_stop_reason?: string;
  eligible_candidates_count?: number;
  skipped_candidates_count?: number;
  skipped_reasons_summary?: Record<string, number>;
  candidate_selection_summary?: {
    matched_event?: string | null;
    matched_category?: string | null;
    selected_template?: string | null;
    would_send?: boolean;
    blocked_by_guard?: boolean;
    delay_reason?: string | null;
  } | null;
  last_manual_cycle_at?: string | null;
  last_send_result?: string | null;
  last_provider_diagnostics?: {
    delivery_summary?: string | null;
    possible_failure_reason?: string | null;
    diagnostics_errors?: string[];
  } | null;
}

interface MonitoringSliceState {
  state: LiveLoadState;
  safety: typeof operationsFixture.safety | null;
  funnel: typeof operationsFixture.funnel | null;
  lastCycle: typeof operationsFixture.lastCycle | null;
  loadedAt: number | null;
  error: string | null;
}

const STALE_AFTER_MS = 60_000;

const operationsFixture = {
  snapshot: {
    status: "Fresh" as SnapshotStatus,
    loadedAgo: "18s ago",
    staleCards: ["Каналы отправки"],
  },
  health: {
    api: "OK",
    db: "Подключено",
    systemStatus: "OK" as SystemStatus,
  },
  safety: {
    operationMode: "MANUAL ONLY" as OperationMode,
    risk: "GUARDED" as RiskStatus,
    automation: false,
    background: false,
    cron: false,
    queue: false,
    bulk: false,
    emergencyStop: true,
    emergencyStopReason: "автоматизация выключена; доступны только ручные защищенные операции",
  },
  staging: {
    foundationEnabled: false,
    stagingMode: true,
    activeExecution: false,
    maxRecordsPerCycle: 1,
    testRecipientsConfigured: true,
    testRecipientCount: 2,
    dryRunRequired: true,
    dryRunEnforced: false,
    guards: [
      "нет активного выполнения scheduler",
      "нет фоновых бесконечных циклов",
      "максимум 1 запись за цикл",
      "только TEST_RECIPIENTS",
      "требуется FLOWSELL_DRY_RUN",
    ],
  },
  adapters: {
    status: "Stale" as SnapshotStatus,
    primaryChannel: "max",
    fallbackChain: ["telegram", "whatsapp"],
    providerAccess: false,
    sendAdapterCalled: false,
    items: [
      {
        channel: "MAX",
        configured: false,
        foundationReady: true,
        realSendEnabled: false,
        state: "not_configured",
        note: "учетные данные MAX не настроены",
      },
      {
        channel: "Telegram",
        configured: false,
        foundationReady: false,
        realSendEnabled: false,
        state: "preview_only",
        note: "только заглушка канала",
      },
      {
        channel: "WhatsApp",
        configured: false,
        foundationReady: false,
        realSendEnabled: false,
        state: "preview_only",
        note: "только заглушка канала",
      },
    ],
  },
  funnel: {
    eligible: 42,
    skipped: 8,
    skippedReasons: [
      ["рассчитанная задержка еще не истекла", 5],
      ["подходящий сценарий не найден", 3],
    ] as [string, number][],
    candidate: {
      matchedEvent: "review_new_client_60m",
      matchedCategory: "new_client",
      selectedTemplate: "review_new_client_60m_template",
      wouldSend: true,
      blockedByGuard: false,
      delayReason: "рассчитанная задержка истекла",
    },
  },
  lastCycle: {
    state: "empty" as "empty" | "failed" | "sent",
    lastSendResult: "Ручной запуск не зафиксирован",
    lastManualCycleAt: null as string | null,
    diagnostics: null as null | {
      deliverySummary: string;
      possibleFailureReason: string;
      errors: string[];
    },
  },
};

const LOADING_LABEL = "Загрузка...";

const boolLabel = (value: boolean) => (value ? "Включено" : "Выключено");
const availabilityLabel = (value: boolean) => (value ? "Доступно" : "Недоступно");

function statusLabel(status: SystemStatus | RiskStatus | SnapshotStatus | OperationMode | "Empty" | "Degraded") {
  const labels: Record<string, string> = {
    OK: "Система работает",
    DEGRADED: "Есть проблемы",
    UNKNOWN: "Неизвестно",
    LOW: "Низкий",
    GUARDED: "Под контролем",
    SAFE: "Безопасный",
    "MANUAL ONLY": "Только вручную",
    "AUTOMATION ENABLED": "Автоматизация включена",
    Fresh: "Актуально",
    Stale: "Данные устарели",
    Empty: "Пусто",
    Degraded: "Есть проблемы",
  };
  return labels[status] ?? status;
}

function loadedAgoLabel(loadedAt: number | null, now: number) {
  if (!loadedAt) return LOADING_LABEL;
  const seconds = Math.max(0, Math.round((now - loadedAt) / 1000));
  if (seconds < 60) return `${seconds} сек. назад`;
  return `${Math.floor(seconds / 60)} мин. назад`;
}

function useHealthSlice(): HealthSliceState & { stale: boolean; loadedAgo: string } {
  const [state, setState] = useState<HealthSliceState>({
    api: "loading",
    db: "loading",
    apiLabel: LOADING_LABEL,
    dbLabel: LOADING_LABEL,
    loadedAt: null,
    error: null,
  });
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const [health, db] = await Promise.allSettled([
        apiClient.get<{ status?: string }>("/health", { timeout: 15_000 }),
        apiClient.get<{ status?: string; database?: string }>("/health/db", { timeout: 15_000 }),
      ]);

      if (cancelled) return;

      const healthOk = health.status === "fulfilled" && health.value.data?.status === "ok";
      const dbConnected =
        db.status === "fulfilled" && db.value.data?.database === "connected";
      const firstError =
        health.status === "rejected"
          ? getErrorMessage(health.reason)
          : db.status === "rejected"
            ? getErrorMessage(db.reason)
            : null;

      setState({
        api: healthOk ? "connected" : "unavailable",
        db: dbConnected ? "connected" : "unavailable",
        apiLabel: healthOk ? "ОК" : "Недоступно",
        dbLabel: dbConnected ? "Подключено" : "Недоступно",
        loadedAt: Date.now(),
        error: firstError,
      });
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 10_000);
    return () => window.clearInterval(id);
  }, []);

  const loadedAgo = useMemo(() => {
    return loadedAgoLabel(state.loadedAt, now);
  }, [now, state.loadedAt]);

  return {
    ...state,
    stale: state.loadedAt !== null && now - state.loadedAt > STALE_AFTER_MS,
    loadedAgo,
  };
}

function toStagingFixture(data: StagingStatusResponse): typeof operationsFixture.staging {
  return {
    foundationEnabled: Boolean(data.foundation_enabled),
    stagingMode: Boolean(data.staging_mode),
    activeExecution: Boolean(data.active_execution_enabled),
    maxRecordsPerCycle: data.max_records_per_cycle ?? 1,
    testRecipientsConfigured: Boolean(data.test_recipients_configured),
    testRecipientCount: data.test_recipient_count ?? 0,
    dryRunRequired: data.dry_run_required ?? true,
    dryRunEnforced: Boolean(data.dry_run_enforced),
    guards: Array.isArray(data.safety_guards) ? data.safety_guards : [],
  };
}

function useStagingSlice(): StagingSliceState & { stale: boolean; loadedAgo: string } {
  const [state, setState] = useState<StagingSliceState>({
    state: "loading",
    data: null,
    loadedAt: null,
    error: null,
  });
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const { data } = await apiClient.get<StagingStatusResponse>("/scheduler/staging-status", {
          timeout: 15_000,
        });
        if (cancelled) return;
        setState({
          state: "connected",
          data: toStagingFixture(data),
          loadedAt: Date.now(),
          error: null,
        });
      } catch (error) {
        if (cancelled) return;
        setState({
          state: "unavailable",
          data: null,
          loadedAt: Date.now(),
          error: getErrorMessage(error),
        });
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 10_000);
    return () => window.clearInterval(id);
  }, []);

  const loadedAgo = useMemo(() => {
    return loadedAgoLabel(state.loadedAt, now);
  }, [now, state.loadedAt]);

  return {
    ...state,
    stale: state.loadedAt !== null && now - state.loadedAt > STALE_AFTER_MS,
    loadedAgo,
  };
}

function toAdaptersFixture(data: DeliveryAdaptersStatusResponse): typeof operationsFixture.adapters {
  return {
    status: "Fresh",
    primaryChannel: data.primary_channel ?? "неизвестно",
    fallbackChain: Array.isArray(data.fallback_chain) ? data.fallback_chain : [],
    providerAccess: Boolean(data.provider_access),
    sendAdapterCalled: Boolean(data.send_adapter_called),
    items: (data.adapters ?? []).map((adapter) => ({
      channel: adapter.channel ?? "неизвестно",
      configured: Boolean(adapter.configured),
      foundationReady: Boolean(adapter.foundation_ready),
      realSendEnabled: Boolean(adapter.real_send_enabled),
      state: adapter.health?.state ?? "неизвестно",
      note: adapter.health?.errors?.[0] ?? "Ошибки состояния канала не возвращены",
    })),
  };
}

function useAdaptersSlice(): AdaptersSliceState & { stale: boolean; loadedAgo: string } {
  const [state, setState] = useState<AdaptersSliceState>({
    state: "loading",
    data: null,
    guards: [],
    loadedAt: null,
    error: null,
  });
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const { data } = await apiClient.get<DeliveryAdaptersStatusResponse>(
          "/scheduler/adapters-status.json",
          { timeout: 15_000 },
        );
        if (cancelled) return;
        setState({
          state: "connected",
          data: toAdaptersFixture(data),
          guards: Array.isArray(data.safety_guards) ? data.safety_guards : [],
          loadedAt: Date.now(),
          error: null,
        });
      } catch (error) {
        if (cancelled) return;
        setState({
          state: "unavailable",
          data: null,
          guards: [],
          loadedAt: Date.now(),
          error: getErrorMessage(error),
        });
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 10_000);
    return () => window.clearInterval(id);
  }, []);

  const loadedAgo = useMemo(() => {
    return loadedAgoLabel(state.loadedAt, now);
  }, [now, state.loadedAt]);

  return {
    ...state,
    stale: state.loadedAt !== null && now - state.loadedAt > STALE_AFTER_MS,
    loadedAgo,
  };
}

function toMonitoringSlice(data: SchedulerMonitoringStatusResponse): Pick<
  MonitoringSliceState,
  "safety" | "funnel" | "lastCycle"
> {
  const diagnostics = data.last_provider_diagnostics;
  const lastSendResult = data.last_send_result || "Ручной запуск не зафиксирован";
  const hasManualCycle = Boolean(data.last_manual_cycle_at);
  const failed =
    lastSendResult === "attempted_not_sent" ||
    lastSendResult === "blocked" ||
    Boolean(diagnostics?.diagnostics_errors?.length);

  return {
    safety: {
      ...operationsFixture.safety,
      automation: Boolean(data.automation_enabled),
      background: Boolean(data.background_execution_enabled),
      cron: Boolean(data.cron_execution_enabled),
      queue: Boolean(data.queue_execution_enabled),
      bulk: Boolean(data.bulk_execution_enabled),
      emergencyStop: Boolean(data.emergency_stop_active),
      emergencyStopReason:
        data.emergency_stop_reason || "Причина аварийной остановки не возвращена",
    },
    funnel: {
      eligible: data.eligible_candidates_count ?? 0,
      skipped: data.skipped_candidates_count ?? 0,
      skippedReasons: Object.entries(data.skipped_reasons_summary ?? {}),
      candidate: {
        matchedEvent: data.candidate_selection_summary?.matched_event || "Кандидат не выбран",
        matchedCategory: data.candidate_selection_summary?.matched_category || "нет",
        selectedTemplate: data.candidate_selection_summary?.selected_template || "нет",
        wouldSend: Boolean(data.candidate_selection_summary?.would_send),
        blockedByGuard: Boolean(data.candidate_selection_summary?.blocked_by_guard),
        delayReason: data.candidate_selection_summary?.delay_reason || "нет",
      },
    },
    lastCycle: {
      state: hasManualCycle ? (failed ? "failed" : "sent") : "empty",
      lastSendResult: hasManualCycle ? lastSendResult : "Ручной запуск не зафиксирован",
      lastManualCycleAt: data.last_manual_cycle_at || null,
      diagnostics: diagnostics
        ? {
            deliverySummary: diagnostics.delivery_summary || "Сводка доставки не возвращена",
            possibleFailureReason:
              diagnostics.possible_failure_reason || "Причина сбоя не возвращена",
            errors: diagnostics.diagnostics_errors ?? [],
          }
        : null,
    },
  };
}

function useMonitoringSlice(): MonitoringSliceState & { stale: boolean; loadedAgo: string } {
  const [state, setState] = useState<MonitoringSliceState>({
    state: "loading",
    safety: null,
    funnel: null,
    lastCycle: null,
    loadedAt: null,
    error: null,
  });
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const { data } = await apiClient.get<SchedulerMonitoringStatusResponse>(
          "/scheduler/monitoring/status",
          { timeout: 30_000 },
        );
        if (cancelled) return;
        const mapped = toMonitoringSlice(data);
        setState({
          state: "connected",
          safety: mapped.safety,
          funnel: mapped.funnel,
          lastCycle: mapped.lastCycle,
          loadedAt: Date.now(),
          error: null,
        });
      } catch (error) {
        if (cancelled) return;
        setState({
          state: "unavailable",
          safety: null,
          funnel: null,
          lastCycle: null,
          loadedAt: Date.now(),
          error: getErrorMessage(error),
        });
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 10_000);
    return () => window.clearInterval(id);
  }, []);

  const loadedAgo = useMemo(() => {
    return loadedAgoLabel(state.loadedAt, now);
  }, [now, state.loadedAt]);

  return {
    ...state,
    stale: state.loadedAt !== null && now - state.loadedAt > STALE_AFTER_MS,
    loadedAgo,
  };
}

function statusTone(status: SystemStatus | RiskStatus | SnapshotStatus | OperationMode): Tone {
  if (status === "OK" || status === "LOW" || status === "SAFE" || status === "Fresh") {
    return "success";
  }
  if (status === "DEGRADED" || status === "AUTOMATION ENABLED") {
    return "destructive";
  }
  if (status === "GUARDED" || status === "MANUAL ONLY" || status === "Stale") {
    return "secondary";
  }
  return "outline";
}

function StatusBadge({
  label,
  value,
}: {
  label: string;
  value: SystemStatus | RiskStatus | SnapshotStatus | OperationMode;
}) {
  return (
    <Badge variant={statusTone(value)} className="gap-1">
      <span className="text-muted-foreground">{label}</span>
      {statusLabel(value)}
    </Badge>
  );
}

function Metric({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string | number;
  tone?: "default" | "success" | "warning" | "muted";
}) {
  return (
    <div className="rounded-md border border-border bg-muted/20 p-3">
      <div
        className={cn(
          "text-lg font-semibold",
          tone === "success" && "text-green-300",
          tone === "warning" && "text-amber-200",
          tone === "muted" && "text-muted-foreground",
        )}
      >
        {value}
      </div>
      <div className="mt-1 text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

function SectionTitle({
  title,
  status,
}: {
  title: string;
  status?: SnapshotStatus | "Empty" | "Degraded";
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <CardTitle>{title}</CardTitle>
      {status && (
        <Badge variant={status === "Fresh" ? "success" : status === "Empty" ? "outline" : "secondary"}>
          {statusLabel(status)}
        </Badge>
      )}
    </div>
  );
}

export function OperationsControlCenterPage() {
  const data = operationsFixture;
  const health = useHealthSlice();
  const staging = useStagingSlice();
  const adapters = useAdaptersSlice();
  const monitoring = useMonitoringSlice();
  const stagingData = staging.data ?? data.staging;
  const adaptersData = adapters.data ?? data.adapters;
  const safetyData = monitoring.safety ?? data.safety;
  const funnelData = monitoring.funnel ?? data.funnel;
  const lastCycleData = monitoring.lastCycle ?? data.lastCycle;
  const liveSystemStatus: SystemStatus =
    health.api === "loading" || health.db === "loading"
      ? "UNKNOWN"
      : health.api === "connected" && health.db === "connected"
        ? "OK"
        : "DEGRADED";
  const liveSnapshotStatus: SnapshotStatus = health.stale ? "Stale" : data.snapshot.status;
  const failedLastCycle = lastCycleData.state === "failed";
  const showSnapshotStaleBanner =
    liveSnapshotStatus === "Stale" || staging.stale || adapters.stale || monitoring.stale;
  const showSystemDegradedBanner = liveSystemStatus === "DEGRADED";
  const allGuards = Array.from(
    new Set([
      ...(staging.data?.guards ?? []),
      ...adapters.guards,
      "Данные доступны только для чтения",
      "сервисы отправки не вызываются",
      "путь выполнения не запускается",
    ]),
  );

  return (
    <main className="mx-auto max-w-7xl space-y-6 px-4 py-6">
      <section className="space-y-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Центр операционного контроля
            </p>
            <h2 className="mt-1 text-2xl font-semibold tracking-tight">
              Операторская панель
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
              Показывает состояние системы, очереди и каналов отправки.
              <br />
              Действия с этого экрана не запускаются.
            </p>
          </div>
          <div className="flex flex-wrap gap-2 lg:justify-end">
            <StatusBadge label="Система" value={liveSystemStatus} />
            <StatusBadge label="Риск" value={data.safety.risk} />
            <StatusBadge label="Состояние данных" value={liveSnapshotStatus} />
            <StatusBadge label="Режим работы" value={data.safety.operationMode} />
          </div>
        </div>
      </section>

      {(showSnapshotStaleBanner || showSystemDegradedBanner) && (
        <section className="space-y-3">
          {showSnapshotStaleBanner && (
            <div className="flex items-start gap-3 rounded-lg border border-amber-500/40 bg-amber-500/10 p-4 text-sm">
              <Clock3 className="mt-0.5 h-4 w-4 shrink-0 text-amber-200" />
              <div>
                <p className="font-medium text-amber-100">Данные устарели</p>
                <p className="mt-1 text-muted-foreground">
                  Некоторые карточки могут быть старше основного состояния данных. Значения остаются видимыми.
                </p>
              </div>
            </div>
          )}
          {showSystemDegradedBanner && (
            <div className="flex items-start gap-3 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-200" />
              <div>
                <p className="font-medium text-red-200">Есть проблемы</p>
                <p className="mt-1 text-muted-foreground">
                  Часть обязательных данных статуса недоступна или работает с ошибками.
                </p>
              </div>
            </div>
          )}
        </section>
      )}

      <section className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
        <Card>
          <CardHeader>
            <SectionTitle title="Состояние платформы" status={liveSnapshotStatus} />
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <Metric
                label="/health"
                value={health.apiLabel}
                tone={health.api === "connected" ? "success" : health.api === "loading" ? "muted" : "warning"}
              />
              <Metric
                label="/health/db"
                value={health.dbLabel}
                tone={health.db === "connected" ? "success" : health.db === "loading" ? "muted" : "warning"}
              />
            </div>
            {health.error && (
              <p className="text-xs text-amber-200">Данные состояния платформы недоступны: {health.error}</p>
            )}
            <p className="text-xs text-muted-foreground">
              {health.loadedAt ? `Обновлено ${health.loadedAgo}` : "Загрузка данных платформы"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <SectionTitle title="Безопасность" status={monitoring.stale ? "Stale" : data.snapshot.status} />
          </CardHeader>
          <CardContent className="space-y-4">
            {monitoring.state === "loading" && (
              <div className="rounded-md border border-border bg-muted/20 p-3 text-sm text-muted-foreground">
                Загрузка данных безопасности...
              </div>
            )}
            {monitoring.state === "unavailable" && (
              <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm">
                <p className="font-medium text-amber-100">Данные безопасности недоступны</p>
                <p className="mt-1 text-muted-foreground">{monitoring.error}</p>
              </div>
            )}
            <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
              <Metric
                label="Автоматизация"
                value={monitoring.state === "loading" ? LOADING_LABEL : boolLabel(safetyData.automation)}
                tone={monitoring.state === "loading" ? "muted" : "success"}
              />
              <Metric
                label="Фоновый режим"
                value={monitoring.state === "loading" ? LOADING_LABEL : boolLabel(safetyData.background)}
                tone={monitoring.state === "loading" ? "muted" : "success"}
              />
              <Metric
                label="Расписание"
                value={monitoring.state === "loading" ? LOADING_LABEL : boolLabel(safetyData.cron)}
                tone={monitoring.state === "loading" ? "muted" : "success"}
              />
              <Metric
                label="Очередь"
                value={monitoring.state === "loading" ? LOADING_LABEL : boolLabel(safetyData.queue)}
                tone={monitoring.state === "loading" ? "muted" : "success"}
              />
              <Metric
                label="Пакетный режим"
                value={monitoring.state === "loading" ? LOADING_LABEL : boolLabel(safetyData.bulk)}
                tone={monitoring.state === "loading" ? "muted" : "success"}
              />
            </div>
            <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm">
              <div className="flex items-center gap-2 font-medium text-amber-100">
                <ShieldCheck className="h-4 w-4" />
                Аварийная остановка {monitoring.state === "loading" ? LOADING_LABEL : boolLabel(safetyData.emergencyStop)}
              </div>
              <p className="mt-1 text-muted-foreground">{safetyData.emergencyStopReason}</p>
            </div>
            <div className="rounded-md border border-border bg-muted/20 p-3 text-sm">
              <p className="font-medium">Ручной запуск</p>
              <p className="mt-1 text-muted-foreground">Запуск вручную с этого экрана недоступен</p>
            </div>
            <p className="text-xs text-muted-foreground">
              {monitoring.loadedAt ? `Обновлено ${monitoring.loadedAgo}` : "Загрузка данных системы"}
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <Card>
          <CardHeader>
            <SectionTitle title="Ограничения тестового режима" status={staging.stale ? "Stale" : data.snapshot.status} />
          </CardHeader>
          <CardContent className="space-y-4">
            {staging.state === "loading" && (
              <div className="rounded-md border border-border bg-muted/20 p-3 text-sm text-muted-foreground">
                Загрузка ограничений тестового режима...
              </div>
            )}
            {staging.state === "unavailable" && (
              <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm">
                <p className="font-medium text-amber-100">Статус тестового режима недоступен</p>
                <p className="mt-1 text-muted-foreground">{staging.error}</p>
              </div>
            )}
            <div className="grid grid-cols-2 gap-3">
              <Metric
                label="Тестовый режим"
                value={staging.state === "loading" ? LOADING_LABEL : boolLabel(stagingData.stagingMode)}
                tone={staging.state === "loading" ? "muted" : "default"}
              />
              <Metric
                label="Лимит записей"
                value={staging.state === "loading" ? LOADING_LABEL : stagingData.maxRecordsPerCycle}
                tone={staging.state === "loading" ? "muted" : "default"}
              />
              <Metric
                label="Тестовые получатели"
                value={staging.state === "loading" ? LOADING_LABEL : stagingData.testRecipientCount}
                tone={staging.state === "loading" ? "muted" : "default"}
              />
              <Metric
                label="Активная обработка"
                value={staging.state === "loading" ? LOADING_LABEL : boolLabel(stagingData.activeExecution)}
                tone={staging.state === "loading" ? "muted" : "success"}
              />
            </div>
            <div className="rounded-md border border-border bg-muted/20 p-3">
              <p className="text-sm font-medium">Ограничение проверочного режима</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Требуется: {staging.state === "loading" ? LOADING_LABEL : availabilityLabel(stagingData.dryRunRequired)} · Принудительно:{" "}
                {staging.state === "loading" ? LOADING_LABEL : availabilityLabel(stagingData.dryRunEnforced)}
              </p>
            </div>
            {staging.state === "connected" && stagingData.guards.length === 0 && (
              <div className="rounded-md border border-dashed border-border bg-muted/20 p-3 text-sm text-muted-foreground">
                Ограничения тестового режима не вернулись.
              </div>
            )}
            <details className="rounded-md border border-border bg-muted/20 p-3">
              <summary className="cursor-pointer text-sm font-medium">Показать детали ограничений</summary>
              <ul className="mt-3 space-y-1 text-sm text-muted-foreground">
                {stagingData.guards.map((guard) => (
                  <li key={guard}>{guard}</li>
                ))}
              </ul>
            </details>
            <p className="text-xs text-muted-foreground">
              {staging.loadedAt ? `Обновлено ${staging.loadedAgo}` : "Загрузка данных тестового режима"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <SectionTitle title="Каналы отправки" status={adapters.stale ? "Stale" : data.snapshot.status} />
          </CardHeader>
          <CardContent className="space-y-4">
            {adapters.state === "loading" && (
              <div className="rounded-md border border-border bg-muted/20 p-3 text-sm text-muted-foreground">
                Загрузка каналов отправки...
              </div>
            )}
            {adapters.state === "unavailable" && (
              <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm">
                <p className="font-medium text-amber-100">Каналы отправки недоступны</p>
                <p className="mt-1 text-muted-foreground">{adapters.error}</p>
              </div>
            )}
            <div className="flex flex-wrap gap-2 text-sm">
              <Badge variant="secondary">Основной: {adaptersData.primaryChannel}</Badge>
              <Badge variant="outline">
                Резерв: {adaptersData.fallbackChain.length > 0 ? adaptersData.fallbackChain.join(" -> ") : "Нет"}
              </Badge>
              <Badge variant="outline">Доступ к сервису отправки: {boolLabel(adaptersData.providerAccess)}</Badge>
              <Badge variant="outline">Канал отправки: {boolLabel(adaptersData.sendAdapterCalled)}</Badge>
            </div>
            {adapters.state === "connected" && adaptersData.items.length === 0 ? (
              <div className="rounded-md border border-dashed border-border bg-muted/20 p-6 text-center text-sm text-muted-foreground">
                Каналы отправки не вернулись.
              </div>
            ) : (
              <div className="grid gap-3 md:grid-cols-3">
                {adaptersData.items.map((adapter) => (
                  <div key={adapter.channel} className="rounded-md border border-border bg-muted/20 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium">{adapter.channel}</p>
                      <Badge variant={adapter.foundationReady ? "success" : "secondary"}>
                        {adapter.state}
                      </Badge>
                    </div>
                    <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
                      <dt className="text-muted-foreground">Настроен</dt>
                      <dd>{availabilityLabel(adapter.configured)}</dd>
                      <dt className="text-muted-foreground">Базовая готовность</dt>
                      <dd>{availabilityLabel(adapter.foundationReady)}</dd>
                      <dt className="text-muted-foreground">Реальная отправка</dt>
                      <dd>{boolLabel(adapter.realSendEnabled)}</dd>
                    </dl>
                    <details className="mt-3 text-sm">
                      <summary className="cursor-pointer text-muted-foreground">Заметка о состоянии</summary>
                      <p className="mt-2 text-muted-foreground">{adapter.note}</p>
                    </details>
                  </div>
                ))}
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              {adapters.loadedAt ? `Обновлено ${adapters.loadedAgo}` : "Загрузка данных каналов отправки"}
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <SectionTitle title="Очередь обработки" status={monitoring.stale ? "Stale" : data.snapshot.status} />
          </CardHeader>
          <CardContent className="space-y-4">
            {monitoring.state === "loading" && (
              <div className="rounded-md border border-border bg-muted/20 p-3 text-sm text-muted-foreground">
                Загрузка очереди обработки...
              </div>
            )}
            {monitoring.state === "unavailable" && (
              <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm">
                <p className="font-medium text-amber-100">Очередь обработки недоступна</p>
                <p className="mt-1 text-muted-foreground">{monitoring.error}</p>
              </div>
            )}
            <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
              <Metric
                label="Готовы к обработке"
                value={monitoring.state === "loading" ? LOADING_LABEL : funnelData.eligible}
                tone={monitoring.state === "loading" ? "muted" : "success"}
              />
              <Metric
                label="Пропущено"
                value={monitoring.state === "loading" ? LOADING_LABEL : funnelData.skipped}
                tone={monitoring.state === "loading" ? "muted" : "warning"}
              />
              <Metric
                label="Кандидат"
                value={monitoring.state === "loading" ? LOADING_LABEL : funnelData.candidate.matchedEvent}
                tone={monitoring.state === "loading" ? "muted" : "default"}
              />
            </div>
            {monitoring.state === "connected" && funnelData.candidate.matchedEvent === "Кандидат не выбран" && (
              <div className="rounded-md border border-dashed border-border bg-muted/20 p-3 text-sm text-muted-foreground">
                Кандидат не выбран.
              </div>
            )}
            <div className="rounded-md border border-border">
              {funnelData.skippedReasons.map(([reason, count]) => (
                <div
                  key={reason}
                  className="flex items-center justify-between border-b border-border px-3 py-2 text-sm last:border-b-0"
                >
                  <span className="text-muted-foreground">{reason}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
            <details className="rounded-md border border-border bg-muted/20 p-3">
              <summary className="cursor-pointer text-sm font-medium">Показать детали кандидата</summary>
              <div className="mt-3 space-y-1 text-sm text-muted-foreground">
                <p>Шаблон: {funnelData.candidate.selectedTemplate}</p>
                <p>Категория: {funnelData.candidate.matchedCategory}</p>
                <p>Причина задержки: {funnelData.candidate.delayReason}</p>
              </div>
            </details>
            <p className="text-xs text-muted-foreground">
              {monitoring.loadedAt ? `Обновлено ${monitoring.loadedAgo}` : "Загрузка данных системы"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <SectionTitle title="Последняя операция" status={lastCycleData.state === "empty" ? "Empty" : monitoring.stale ? "Stale" : data.snapshot.status} />
          </CardHeader>
          <CardContent className="space-y-4">
            {monitoring.state === "loading" && (
              <div className="rounded-md border border-border bg-muted/20 p-3 text-sm text-muted-foreground">
                Загрузка данных последней операции...
              </div>
            )}
            {monitoring.state === "unavailable" && (
              <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm">
                <p className="font-medium text-amber-100">Данные последней операции недоступны</p>
                <p className="mt-1 text-muted-foreground">{monitoring.error}</p>
              </div>
            )}
            {lastCycleData.state === "empty" ? (
              <div className="rounded-md border border-dashed border-border bg-muted/20 p-6 text-center">
                <Info className="mx-auto h-8 w-8 text-muted-foreground" />
                <p className="mt-2 text-sm font-medium">{lastCycleData.lastSendResult}</p>
                {!lastCycleData.diagnostics && (
                  <p className="mt-1 text-sm text-muted-foreground">
                    Диагностика отправки в текущем процессе не записана.
                  </p>
                )}
              </div>
            ) : null}
            {lastCycleData.diagnostics && (
              <details open={failedLastCycle} className="rounded-md border border-border bg-muted/20 p-3">
                <summary className="cursor-pointer text-sm font-medium">Диагностика отправки</summary>
                <div className="mt-3 space-y-1 text-sm text-muted-foreground">
                  <p>{lastCycleData.diagnostics.deliverySummary}</p>
                  <p>{lastCycleData.diagnostics.possibleFailureReason}</p>
                  {lastCycleData.diagnostics.errors.map((error) => (
                    <p key={error}>{error}</p>
                  ))}
                </div>
              </details>
            )}
            <p className="text-xs text-muted-foreground">
              {monitoring.loadedAt ? `Обновлено ${monitoring.loadedAgo}` : "Загрузка данных системы"}
            </p>
          </CardContent>
        </Card>
      </section>

      <section>
        <Card>
          <CardHeader>
            <SectionTitle title="Активные ограничения" status={data.snapshot.status} />
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-2 md:grid-cols-2">
              {allGuards.slice(0, 6).map((guard) => (
                <div key={guard} className="flex items-start gap-2 text-sm">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-green-300" />
                  <span className="text-muted-foreground">{guard}</span>
                </div>
              ))}
            </div>
            <details className="rounded-md border border-border bg-muted/20 p-3">
              <summary className="cursor-pointer text-sm font-medium">Показать все ограничения</summary>
              <ul className="mt-3 space-y-1 text-sm text-muted-foreground">
                {allGuards.map((guard) => (
                  <li key={guard}>{guard}</li>
                ))}
              </ul>
            </details>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
