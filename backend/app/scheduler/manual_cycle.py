"""Isolated manual single-cycle scheduler execution.

This module performs one explicitly confirmed scheduler cycle with hard safety
guards. It is not connected to cron, background loops, queues, retries, workers,
or bulk campaign execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.integrations.flowsell.send_adapter import FlowSellControlledSendResult, FlowSellSendAdapter
from app.integrations.flowsell.templates import load_template_catalog
from app.scheduler import setup as scheduler_setup
from app.scheduler.execution_preview import (
    SchedulerExecutionCandidatePlan,
    SchedulerExecutionPreviewInput,
    build_scheduler_execution_preview,
)
from app.scheduler.monitoring import record_manual_cycle_result
from app.scheduler.staging_execution import StagingProviderDiagnostics, build_staging_provider_diagnostics


@dataclass(frozen=True, slots=True)
class ManualCycleInput:
    confirm_manual_cycle: bool = False
    flow_type: str = "all"
    max_candidates: int = 10
    reminder_horizon_hours: int = 24
    channel: str = "sms"


@dataclass(frozen=True, slots=True)
class ManualCycleSkippedCandidate:
    record_id: int
    yclients_record_id: int
    client_name: str
    service_name: str
    flow_type: str
    matched_category: str | None
    matched_event: str | None
    selected_template: str | None
    would_send: bool
    blocked_by_guard: bool
    skip_reason: str
    guard_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ManualCycleExecutedSend:
    record_id: int
    yclients_record_id: int
    client_name: str
    service_name: str
    matched_category: str | None
    matched_event: str | None
    selected_template: str | None
    recipient_used: str | None
    chat_id: str | None
    message_id: str | None
    sent: bool
    provider: str
    provider_response_preview: str | None
    rendered_text: str | None
    validation_errors: list[str]
    warnings: list[str]
    provider_diagnostics: StagingProviderDiagnostics | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["provider_diagnostics"] = (
            self.provider_diagnostics.to_dict() if self.provider_diagnostics else None
        )
        return data


@dataclass(frozen=True, slots=True)
class ManualCycleResult:
    manual_trigger_only: bool
    single_cycle_execution: bool
    max_eligible_sends_per_cycle: int
    confirm_manual_cycle: bool
    blocked: bool
    dry_run: bool
    automation_enabled_before: bool
    automation_enabled_after: bool
    candidates_found: int
    eligible_candidates_found: int
    skipped_candidates: list[ManualCycleSkippedCandidate]
    executed_send: ManualCycleExecutedSend | None
    execution_summary: str
    execution_timeline: list[str]
    safety_guards: list[str]
    guard_errors: list[str]
    provider_access: bool
    send_adapter_called: bool
    send_pipeline_called: bool
    background_execution: bool
    cron_execution: bool
    queue_execution: bool
    bulk_execution: bool

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["skipped_candidates"] = [candidate.to_dict() for candidate in self.skipped_candidates]
        data["executed_send"] = self.executed_send.to_dict() if self.executed_send else None
        return data


async def execute_manual_scheduler_cycle(
    db: AsyncSession,
    cycle_input: ManualCycleInput,
    *,
    settings: Settings | None = None,
    adapter_cls: type[FlowSellSendAdapter] = FlowSellSendAdapter,
) -> ManualCycleResult:
    current = settings or get_settings()
    automation_enabled_before = scheduler_setup.is_automation_enabled()
    timeline = ["manual_cycle_endpoint_invoked", "safety_guards_checked"]
    safety_guards = [
        "manual trigger only",
        "single cycle execution only",
        "maximum 1 eligible send per cycle",
        "TEST_RECIPIENTS[0] recipient only",
        "FLOWSELL_DRY_RUN=false required",
        "automation must remain disabled",
        "emergency stop: blocked when automation is enabled",
        "no background loops/cron execution",
        "no queues/workers/retries",
        "no bulk campaigns",
    ]
    guard_errors = _collect_guard_errors(
        current,
        confirm_manual_cycle=cycle_input.confirm_manual_cycle,
        automation_enabled=automation_enabled_before,
    )

    preview = await build_scheduler_execution_preview(
        db,
        SchedulerExecutionPreviewInput(
            flow_type=cycle_input.flow_type,  # type: ignore[arg-type]
            max_candidates=cycle_input.max_candidates,
            reminder_horizon_hours=cycle_input.reminder_horizon_hours,
        ),
        settings=current,
    )
    timeline.append("candidate_selection_completed")

    eligible = [plan for plan in preview.plans if plan.would_send and not plan.blocked_by_guard]
    skipped = _skipped_candidates(preview.plans, eligible)
    timeline.append("eligible_candidates_filtered")

    if guard_errors:
        return _record_and_return(
            _blocked_result(
                cycle_input=cycle_input,
                current=current,
                automation_enabled_before=automation_enabled_before,
                candidates_found=preview.candidates_found,
                eligible_candidates_found=len(eligible),
                skipped_candidates=skipped,
                timeline=timeline + ["blocked_before_send_adapter"],
                safety_guards=safety_guards,
                guard_errors=guard_errors,
            ),
        )

    if not eligible:
        return _record_and_return(
            _blocked_result(
                cycle_input=cycle_input,
                current=current,
                automation_enabled_before=automation_enabled_before,
                candidates_found=preview.candidates_found,
                eligible_candidates_found=0,
                skipped_candidates=skipped,
                timeline=timeline + ["no_eligible_candidates"],
                safety_guards=safety_guards,
                guard_errors=["no eligible candidates for this manual cycle"],
            ),
        )

    selected = eligible[0]
    skipped.extend(_skip_extra_eligible_candidates(eligible[1:]))
    recipient = current.test_recipient_phones[0]
    timeline.extend(["single_eligible_candidate_selected", "template_values_built", "send_adapter_execution"])

    adapter_event = _adapter_event(selected)
    result = await adapter_cls(settings=current).send_event(
        event=adapter_event,
        phone=recipient,
        values=_template_values(selected),
        service_type=selected.matched_category,
        channel=cycle_input.channel,
    )
    timeline.append("provider_response_received" if result.provider_response_preview else "adapter_result_received")

    diagnostics = None
    if result.message_id:
        diagnostics = await build_staging_provider_diagnostics(message_id=result.message_id, settings=current)
        timeline.append("provider_diagnostics_completed")

    return _record_and_return(
        ManualCycleResult(
            manual_trigger_only=True,
            single_cycle_execution=True,
            max_eligible_sends_per_cycle=1,
            confirm_manual_cycle=cycle_input.confirm_manual_cycle,
            blocked=False,
            dry_run=result.dry_run,
            automation_enabled_before=automation_enabled_before,
            automation_enabled_after=scheduler_setup.is_automation_enabled(),
            candidates_found=preview.candidates_found,
            eligible_candidates_found=len(eligible),
            skipped_candidates=skipped,
            executed_send=_executed_send(selected, result, diagnostics),
            execution_summary="Manual single-cycle completed with one controlled send attempt.",
            execution_timeline=timeline,
            safety_guards=safety_guards,
            guard_errors=[],
            provider_access=bool(result.provider_response_preview or result.message_id),
            send_adapter_called=True,
            send_pipeline_called=False,
            background_execution=False,
            cron_execution=False,
            queue_execution=False,
            bulk_execution=False,
        ),
    )


def _collect_guard_errors(
    settings: Settings,
    *,
    confirm_manual_cycle: bool,
    automation_enabled: bool,
) -> list[str]:
    errors: list[str] = []
    if not confirm_manual_cycle:
        errors.append("confirm_manual_cycle=true is required")
    if settings.FLOWSELL_DRY_RUN:
        errors.append("FLOWSELL_DRY_RUN must be false for manual scheduler cycle")
    if settings.SCHEDULER_STAGING_MAX_RECORDS != 1:
        errors.append("SCHEDULER_STAGING_MAX_RECORDS must be 1")
    if not settings.test_recipient_phones:
        errors.append("TEST_RECIPIENTS must contain at least one phone")
    if automation_enabled:
        errors.append("automation must be disabled before manual scheduler cycle")
    return errors


def _skipped_candidates(
    plans: list[SchedulerExecutionCandidatePlan],
    eligible: list[SchedulerExecutionCandidatePlan],
) -> list[ManualCycleSkippedCandidate]:
    eligible_ids = {plan.yclients_record_id for plan in eligible}
    skipped: list[ManualCycleSkippedCandidate] = []
    for plan in plans:
        if plan.yclients_record_id in eligible_ids:
            continue
        skipped.append(
            _skipped_candidate(
                plan,
                "blocked_by_guard" if plan.blocked_by_guard else "not eligible for this cycle",
            ),
        )
    return skipped


def _skip_extra_eligible_candidates(
    plans: list[SchedulerExecutionCandidatePlan],
) -> list[ManualCycleSkippedCandidate]:
    return [
        _skipped_candidate(plan, "max 1 eligible send per manual cycle; left for a future manual cycle")
        for plan in plans
    ]


def _skipped_candidate(plan: SchedulerExecutionCandidatePlan, reason: str) -> ManualCycleSkippedCandidate:
    return ManualCycleSkippedCandidate(
        record_id=plan.record_id,
        yclients_record_id=plan.yclients_record_id,
        client_name=plan.client_name,
        service_name=plan.service_name,
        flow_type=plan.flow_type,
        matched_category=plan.matched_category,
        matched_event=plan.matched_event,
        selected_template=plan.selected_template,
        would_send=plan.would_send,
        blocked_by_guard=plan.blocked_by_guard,
        skip_reason=reason,
        guard_errors=plan.guard_errors,
    )


def _executed_send(
    plan: SchedulerExecutionCandidatePlan,
    result: FlowSellControlledSendResult,
    diagnostics: StagingProviderDiagnostics | None,
) -> ManualCycleExecutedSend:
    return ManualCycleExecutedSend(
        record_id=plan.record_id,
        yclients_record_id=plan.yclients_record_id,
        client_name=plan.client_name,
        service_name=plan.service_name,
        matched_category=plan.matched_category,
        matched_event=plan.matched_event,
        selected_template=plan.selected_template,
        recipient_used=result.phone,
        chat_id=result.chat_id,
        message_id=result.message_id,
        sent=result.sent,
        provider=result.provider,
        provider_response_preview=result.provider_response_preview,
        rendered_text=result.rendered_text,
        validation_errors=result.validation_errors,
        warnings=result.warnings,
        provider_diagnostics=diagnostics,
    )


def _adapter_event(plan: SchedulerExecutionCandidatePlan) -> str:
    if plan.selected_template:
        return load_template_catalog().get(plan.selected_template).event
    return plan.matched_event or ""


def _template_values(plan: SchedulerExecutionCandidatePlan) -> dict[str, object | None]:
    appointment = _parse_datetime(plan.appointment_datetime)
    return {
        "client_name": plan.client_name,
        "service_name": plan.service_name,
        "appointment_date": appointment.strftime("%d.%m.%Y") if appointment else "дата визита",
        "appointment_time": appointment.strftime("%H:%M") if appointment else "время визита",
        "master_name": "мастер",
        "booking_link": "https://example.com/booking-preview",
    }


def _parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _blocked_result(
    *,
    cycle_input: ManualCycleInput,
    current: Settings,
    automation_enabled_before: bool,
    candidates_found: int,
    eligible_candidates_found: int,
    skipped_candidates: list[ManualCycleSkippedCandidate],
    timeline: list[str],
    safety_guards: list[str],
    guard_errors: list[str],
) -> ManualCycleResult:
    return ManualCycleResult(
        manual_trigger_only=True,
        single_cycle_execution=True,
        max_eligible_sends_per_cycle=1,
        confirm_manual_cycle=cycle_input.confirm_manual_cycle,
        blocked=True,
        dry_run=current.FLOWSELL_DRY_RUN,
        automation_enabled_before=automation_enabled_before,
        automation_enabled_after=scheduler_setup.is_automation_enabled(),
        candidates_found=candidates_found,
        eligible_candidates_found=eligible_candidates_found,
        skipped_candidates=skipped_candidates,
        executed_send=None,
        execution_summary="Manual single-cycle blocked by safety guards.",
        execution_timeline=timeline,
        safety_guards=safety_guards,
        guard_errors=guard_errors,
        provider_access=False,
        send_adapter_called=False,
        send_pipeline_called=False,
        background_execution=False,
        cron_execution=False,
        queue_execution=False,
        bulk_execution=False,
    )


def _record_and_return(result: ManualCycleResult) -> ManualCycleResult:
    record_manual_cycle_result(result)
    return result
