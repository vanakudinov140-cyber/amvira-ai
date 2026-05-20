"""Read-only scheduler candidate execution preview.

This module builds a manual preview of scheduler decisions from persisted
records. It never calls send adapters, providers, queues, workers, or background
execution paths.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.client import Client
from app.models.procedure import Procedure
from app.models.record import Record
from app.scheduler.dry_run_planner import PlannerInput, SchedulerDryRunPlan, build_scheduler_dry_run_plan
from app.scheduler.staging_foundation import get_scheduler_staging_status
from app.services.retention import rules

SchedulerExecutionFlow = Literal["all", "review", "reminder"]


@dataclass(frozen=True, slots=True)
class SchedulerExecutionPreviewInput:
    flow_type: SchedulerExecutionFlow = "all"
    max_candidates: int = 10
    reminder_horizon_hours: int = 24


@dataclass(frozen=True, slots=True)
class SchedulerCandidateSource:
    record_id: int
    yclients_record_id: int
    client_id: int | None
    client_name: str
    client_phone: str | None
    service_name: str
    appointment_datetime: datetime
    master_name: str | None
    flow_type: Literal["review", "reminder"]
    reminder_kind: Literal["24h", "2h"] | None = None
    is_new_client: bool = False
    candidate_reason: str = ""


@dataclass(frozen=True, slots=True)
class SchedulerExecutionCandidatePlan:
    record_id: int
    yclients_record_id: int
    client_id: int | None
    client_name: str
    client_phone: str | None
    service_name: str
    appointment_datetime: str
    flow_type: str
    candidate_reason: str
    matched_category: str | None
    matched_event: str | None
    selected_template: str | None
    delay_rule: dict[str, Any] | None
    scheduled_send_at: str | None
    would_send: bool
    blocked_by_guard: bool
    execution_reasoning: list[str]
    guard_errors: list[str]
    planner_reasons: list[str]
    provider_access: bool = False
    send_adapter_called: bool = False
    send_pipeline_called: bool = False
    background_execution: bool = False
    bulk_execution: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SchedulerExecutionPreview:
    read_only: bool
    manual_trigger_only: bool
    dry_run: bool
    provider_access: bool
    send_adapter_called: bool
    send_pipeline_called: bool
    background_execution: bool
    cron_execution: bool
    queue_execution: bool
    bulk_execution: bool
    candidates_found: int
    plans: list[SchedulerExecutionCandidatePlan]
    safety_guards: list[str]
    execution_reasoning: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["plans"] = [plan.to_dict() for plan in self.plans]
        return data


async def build_scheduler_execution_preview(
    db: AsyncSession,
    preview_input: SchedulerExecutionPreviewInput,
    *,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> SchedulerExecutionPreview:
    current = settings or get_settings()
    current_now = now or datetime.now(timezone.utc)
    max_candidates = _clamp(preview_input.max_candidates, minimum=1, maximum=50)
    candidates: list[SchedulerCandidateSource] = []

    if preview_input.flow_type in {"all", "review"}:
        candidates.extend(await _select_review_candidates(db, limit=max_candidates, now=current_now))

    if preview_input.flow_type in {"all", "reminder"}:
        remaining = max_candidates - len(candidates)
        if remaining > 0:
            candidates.extend(
                await _select_reminder_candidates(
                    db,
                    limit=remaining,
                    now=current_now,
                    horizon_hours=_clamp(preview_input.reminder_horizon_hours, minimum=1, maximum=168),
                ),
            )

    plans = [_build_candidate_plan(candidate, current, current_now) for candidate in candidates[:max_candidates]]
    status = get_scheduler_staging_status(current)

    return SchedulerExecutionPreview(
        read_only=True,
        manual_trigger_only=True,
        dry_run=True,
        provider_access=False,
        send_adapter_called=False,
        send_pipeline_called=False,
        background_execution=False,
        cron_execution=False,
        queue_execution=False,
        bulk_execution=False,
        candidates_found=len(plans),
        plans=plans,
        safety_guards=[
            *status.safety_guards,
            "manual execution preview only",
            "planner decisions only",
            "provider and send adapter are not reachable from this endpoint",
        ],
        execution_reasoning=[
            "read_only_candidate_selection",
            "planner_delay_and_template_selection",
            "would_send_calculation_without_provider_access",
            "manual_preview_stops_before_send_pipeline",
        ],
    )


async def _select_review_candidates(
    db: AsyncSession,
    *,
    limit: int,
    now: datetime,
) -> list[SchedulerCandidateSource]:
    row_num = func.row_number().over(
        partition_by=Client.id,
        order_by=(Record.record_datetime.desc(), Record.id.desc()),
    ).label("rn")

    ranked = (
        select(Record.id.label("record_id"), row_num)
        .select_from(Record)
        .join(Client, Client.external_id == Record.client_id)
        .join(Procedure, Procedure.external_id == Record.service_id)
        .where(
            Record.record_datetime.isnot(None),
            Record.record_datetime < now,
            Record.attendance.in_(rules.COMPLETED_ATTENDANCE_VALUES),
            Record.client_id.isnot(None),
            Record.service_id.isnot(None),
        )
        .subquery()
    )
    latest_record_ids = select(ranked.c.record_id).where(ranked.c.rn == 1)
    stmt = (
        select(Record, Client, Procedure)
        .join(Client, Client.external_id == Record.client_id)
        .join(Procedure, Procedure.external_id == Record.service_id)
        .where(Record.id.in_(latest_record_ids))
        .order_by(Record.record_datetime.desc(), Record.id.desc())
        .limit(limit)
    )

    rows = (await db.execute(stmt)).all()
    candidates: list[SchedulerCandidateSource] = []
    for record, client, procedure in rows:
        if record.record_datetime is None:
            continue
        completed_count = await _completed_visit_count(db, record.client_id)
        candidates.append(
            SchedulerCandidateSource(
                record_id=record.id,
                yclients_record_id=record.yclients_record_id,
                client_id=client.id,
                client_name=_client_display_name(client),
                client_phone=client.phone,
                service_name=procedure.name,
                appointment_datetime=record.record_datetime,
                master_name=None,
                flow_type="review",
                is_new_client=completed_count <= 1,
                candidate_reason=(
                    "Последний завершённый визит клиента; подходит для проверки сценария отзыва."
                ),
            ),
        )
    return candidates


async def _select_reminder_candidates(
    db: AsyncSession,
    *,
    limit: int,
    now: datetime,
    horizon_hours: int,
) -> list[SchedulerCandidateSource]:
    horizon_end = now + timedelta(hours=horizon_hours)
    stmt = (
        select(Record, Client, Procedure)
        .join(Client, Client.external_id == Record.client_id)
        .join(Procedure, Procedure.external_id == Record.service_id)
        .where(
            Record.record_datetime.isnot(None),
            Record.record_datetime >= now,
            Record.record_datetime <= horizon_end,
            Record.client_id.isnot(None),
            Record.service_id.isnot(None),
        )
        .order_by(Record.record_datetime.asc(), Record.id.asc())
        .limit(limit)
    )

    rows = (await db.execute(stmt)).all()
    candidates: list[SchedulerCandidateSource] = []
    for record, client, procedure in rows:
        if record.record_datetime is None:
            continue
        hours_until = _hours_between(now, record.record_datetime)
        reminder_kind: Literal["24h", "2h"] = "2h" if hours_until <= 2 else "24h"
        candidates.append(
            SchedulerCandidateSource(
                record_id=record.id,
                yclients_record_id=record.yclients_record_id,
                client_id=client.id,
                client_name=_client_display_name(client),
                client_phone=client.phone,
                service_name=procedure.name,
                appointment_datetime=record.record_datetime,
                master_name=None,
                flow_type="reminder",
                reminder_kind=reminder_kind,
                candidate_reason=(
                    f"Предстоящая запись в горизонте {horizon_hours} ч.; "
                    f"выбран reminder_kind={reminder_kind}."
                ),
            ),
        )
    return candidates


def _build_candidate_plan(
    candidate: SchedulerCandidateSource,
    settings: Settings,
    now: datetime,
) -> SchedulerExecutionCandidatePlan:
    plan = build_scheduler_dry_run_plan(
        PlannerInput(
            flow_type=candidate.flow_type,
            service_name=candidate.service_name,
            client_phone=candidate.client_phone,
            record_id=str(candidate.yclients_record_id),
            is_new_client=candidate.is_new_client,
            reminder_kind=candidate.reminder_kind,
        ),
        settings=settings,
        require_dry_run_guard=False,
    )
    scheduled_send_at = _scheduled_send_at(candidate, plan)
    due_now = scheduled_send_at is not None and _coerce_for_compare(scheduled_send_at, now) <= _coerce_for_compare(now, now)
    blocked_by_guard = bool(plan.guard_errors) or not plan.matched_event or not plan.template_id or not due_now
    reasoning = _execution_reasoning(candidate, plan, scheduled_send_at, due_now)

    return SchedulerExecutionCandidatePlan(
        record_id=candidate.record_id,
        yclients_record_id=candidate.yclients_record_id,
        client_id=candidate.client_id,
        client_name=candidate.client_name,
        client_phone=candidate.client_phone,
        service_name=candidate.service_name,
        appointment_datetime=candidate.appointment_datetime.isoformat(),
        flow_type=candidate.flow_type,
        candidate_reason=candidate.candidate_reason,
        matched_category=plan.matched_category,
        matched_event=plan.matched_event,
        selected_template=plan.template_id,
        delay_rule=asdict(plan.delay_rule) if plan.delay_rule else None,
        scheduled_send_at=scheduled_send_at.isoformat() if scheduled_send_at else None,
        would_send=not blocked_by_guard,
        blocked_by_guard=blocked_by_guard,
        execution_reasoning=reasoning,
        guard_errors=[
            *plan.guard_errors,
            *(["calculated delay is not due yet"] if scheduled_send_at and not due_now else []),
        ],
        planner_reasons=plan.reasons,
    )


def _scheduled_send_at(candidate: SchedulerCandidateSource, plan: SchedulerDryRunPlan) -> datetime | None:
    if plan.delay_rule is None:
        return None
    delay_type = plan.delay_rule.delay_type
    delay_value = plan.delay_rule.delay_value
    if delay_type == "hours_before":
        return candidate.appointment_datetime - timedelta(hours=delay_value)
    if delay_type == "minutes":
        return candidate.appointment_datetime + timedelta(minutes=delay_value)
    if delay_type == "days":
        return candidate.appointment_datetime + timedelta(days=delay_value)
    return None


def _execution_reasoning(
    candidate: SchedulerCandidateSource,
    plan: SchedulerDryRunPlan,
    scheduled_send_at: datetime | None,
    due_now: bool,
) -> list[str]:
    reasoning = [
        candidate.candidate_reason,
        f"Planner selected flow={candidate.flow_type}.",
    ]
    if plan.matched_category:
        reasoning.append(f"Matched category: {plan.matched_category}.")
    if plan.matched_event and plan.template_id:
        reasoning.append(f"Selected event={plan.matched_event}, template={plan.template_id}.")
    if scheduled_send_at is not None:
        state = "уже наступило" if due_now else "ещё не наступило"
        reasoning.append(f"Расчётное время отправки: {scheduled_send_at.isoformat()} ({state}).")
    reasoning.append("Preview stops before send adapter/provider.")
    return reasoning


async def _completed_visit_count(db: AsyncSession, client_external_id: int | None) -> int:
    if client_external_id is None:
        return 0
    return await db.scalar(
        select(func.count(Record.id))
        .select_from(Record)
        .where(
            Record.client_id == client_external_id,
            Record.record_datetime.isnot(None),
            Record.attendance.in_(rules.COMPLETED_ATTENDANCE_VALUES),
        ),
    ) or 0


def _client_display_name(client: Client) -> str:
    name = " ".join(part for part in [client.first_name or "", client.last_name or ""] if part).strip()
    return name if name else "Клиент"


def _hours_between(start: datetime, end: datetime) -> float:
    start_cmp = _coerce_for_compare(start, end)
    end_cmp = _coerce_for_compare(end, end)
    return (end_cmp - start_cmp).total_seconds() / 3600


def _coerce_for_compare(value: datetime, reference: datetime) -> datetime:
    if value.tzinfo is None and reference.tzinfo is not None:
        return value.replace(tzinfo=reference.tzinfo)
    if value.tzinfo is not None and reference.tzinfo is None:
        return value.replace(tzinfo=None)
    return value


def _clamp(value: int, *, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))
