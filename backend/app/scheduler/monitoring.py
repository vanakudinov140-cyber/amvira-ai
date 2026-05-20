"""Read-only scheduler monitoring and observability foundation."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.scheduler import job_state, setup as scheduler_setup
from app.scheduler.execution_preview import SchedulerExecutionPreviewInput, build_scheduler_execution_preview
from app.scheduler.staging_foundation import get_scheduler_staging_status

MAX_HISTORY_ITEMS = 10


@dataclass(frozen=True, slots=True)
class ManualCycleHistoryItem:
    recorded_at: str
    blocked: bool
    sent: bool
    selected_template: str | None
    selected_event: str | None
    provider_delivery_state: str | None
    candidates_found: int
    eligible_candidates_found: int
    skipped_candidates_count: int
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SchedulerMonitoringSnapshot:
    read_only: bool
    automation_enabled: bool
    scheduler_running: bool
    background_execution_enabled: bool
    cron_execution_enabled: bool
    queue_execution_enabled: bool
    bulk_execution_enabled: bool
    emergency_stop_active: bool
    emergency_stop_reason: str
    dry_run: bool
    test_recipients_configured: bool
    test_recipient_count: int
    active_execution_enabled: bool
    last_manual_cycle_at: str | None
    last_execution_timestamp: str | None
    last_send_result: str
    eligible_candidates_count: int
    skipped_candidates_count: int
    skipped_reasons_summary: dict[str, int]
    last_selected_template: str | None
    last_selected_event: str | None
    last_provider_diagnostics: dict[str, Any] | None
    execution_history_summary: list[ManualCycleHistoryItem]
    safety_guards: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["execution_history_summary"] = [item.to_dict() for item in self.execution_history_summary]
        return data


_history: list[ManualCycleHistoryItem] = []
_state: dict[str, Any] = {
    "last_manual_cycle": None,
    "last_manual_cycle_at": None,
}
_lock = Lock()


def record_manual_cycle_result(result: object) -> None:
    """Record a lightweight in-memory summary for read-only monitoring."""
    if not hasattr(result, "to_dict"):
        return
    data = result.to_dict()  # type: ignore[no-any-return]
    now = datetime.now(timezone.utc).isoformat()
    executed_send = data.get("executed_send") or {}
    diagnostics = executed_send.get("provider_diagnostics") or {}
    item = ManualCycleHistoryItem(
        recorded_at=now,
        blocked=bool(data.get("blocked")),
        sent=bool(executed_send.get("sent")) if executed_send else False,
        selected_template=executed_send.get("selected_template"),
        selected_event=executed_send.get("matched_event"),
        provider_delivery_state=diagnostics.get("provider_delivery_state"),
        candidates_found=int(data.get("candidates_found") or 0),
        eligible_candidates_found=int(data.get("eligible_candidates_found") or 0),
        skipped_candidates_count=len(data.get("skipped_candidates") or []),
        summary=str(data.get("execution_summary") or ""),
    )
    with _lock:
        _state["last_manual_cycle"] = data
        _state["last_manual_cycle_at"] = now
        _history.insert(0, item)
        del _history[MAX_HISTORY_ITEMS:]


def clear_monitoring_history() -> None:
    """Test helper: reset process-local monitoring state."""
    with _lock:
        _state["last_manual_cycle"] = None
        _state["last_manual_cycle_at"] = None
        _history.clear()


def get_monitoring_history_summary() -> list[ManualCycleHistoryItem]:
    """Return process-local monitoring history without exposing mutable state."""
    with _lock:
        return list(_history)


async def build_scheduler_monitoring_snapshot(
    db: AsyncSession,
    *,
    settings: Settings | None = None,
) -> SchedulerMonitoringSnapshot:
    current = settings or get_settings()
    automation_enabled = scheduler_setup.is_automation_enabled()
    staging_status = get_scheduler_staging_status(current)
    preview = await build_scheduler_execution_preview(
        db,
        SchedulerExecutionPreviewInput(flow_type="all", max_candidates=50, reminder_horizon_hours=24),
        settings=current,
    )
    eligible_count = sum(1 for plan in preview.plans if plan.would_send and not plan.blocked_by_guard)
    skipped_plans = [plan for plan in preview.plans if not plan.would_send or plan.blocked_by_guard]

    with _lock:
        last_cycle = dict(_state["last_manual_cycle"] or {})
        last_cycle_at = _state["last_manual_cycle_at"]
        history = list(_history)

    executed_send = last_cycle.get("executed_send") or {}
    diagnostics = executed_send.get("provider_diagnostics")
    last_send_result = _last_send_result(last_cycle, executed_send)
    job = job_state.get_job_state()
    last_execution_timestamp = last_cycle_at or _dt_to_str(job.last_job_finished_at or job.last_job_started_at)

    return SchedulerMonitoringSnapshot(
        read_only=True,
        automation_enabled=automation_enabled,
        scheduler_running=scheduler_setup.is_scheduler_running(),
        background_execution_enabled=False,
        cron_execution_enabled=False,
        queue_execution_enabled=False,
        bulk_execution_enabled=False,
        emergency_stop_active=not automation_enabled,
        emergency_stop_reason=(
            "automation disabled; manual guarded operations only"
            if not automation_enabled
            else "automation enabled; manual cycle guard will block"
        ),
        dry_run=current.FLOWSELL_DRY_RUN,
        test_recipients_configured=bool(current.test_recipient_phones),
        test_recipient_count=len(current.test_recipient_phones),
        active_execution_enabled=staging_status.active_execution_enabled,
        last_manual_cycle_at=last_cycle_at,
        last_execution_timestamp=last_execution_timestamp,
        last_send_result=last_send_result,
        eligible_candidates_count=eligible_count,
        skipped_candidates_count=len(skipped_plans),
        skipped_reasons_summary=_skipped_reasons_summary(skipped_plans),
        last_selected_template=executed_send.get("selected_template"),
        last_selected_event=executed_send.get("matched_event"),
        last_provider_diagnostics=diagnostics,
        execution_history_summary=history,
        safety_guards=[
            *staging_status.safety_guards,
            "monitoring endpoint is read-only",
            "provider/send adapter are not called",
            "automation state is not changed",
            "execution path is not started",
        ],
    )


def _skipped_reasons_summary(plans: list[object]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for plan in plans:
        guard_errors = getattr(plan, "guard_errors", None) or []
        if guard_errors:
            for error in guard_errors:
                counter[str(error)] += 1
        else:
            counter["not eligible for this monitoring snapshot"] += 1
    return dict(counter)


def _last_send_result(last_cycle: dict[str, Any], executed_send: dict[str, Any]) -> str:
    if not last_cycle:
        return "no manual cycle recorded in this process"
    if last_cycle.get("blocked"):
        return "blocked"
    if executed_send.get("sent"):
        return "sent"
    if executed_send:
        return "attempted_not_sent"
    return "no_send_executed"


def _dt_to_str(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
