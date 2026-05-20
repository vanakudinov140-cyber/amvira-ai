"""Guarded one-shot automation bridge.

This is a semi-automation layer for a single manually triggered cycle. It
reuses the isolated manual cycle executor and does not enable permanent
automation, cron, background loops, queues, workers, retries, or bulk sends.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.integrations.flowsell.send_adapter import FlowSellSendAdapter
from app.scheduler.manual_cycle import ManualCycleInput, ManualCycleResult, execute_manual_scheduler_cycle
from app.scheduler.monitoring import record_manual_cycle_result


@dataclass(frozen=True, slots=True)
class GuardedAutomationInput:
    confirm_guarded_automation: bool = False
    flow_type: str = "all"
    max_candidates: int = 10
    reminder_horizon_hours: int = 24
    channel: str = "sms"


@dataclass(frozen=True, slots=True)
class GuardedAutomationResult:
    guarded_automation: bool
    manual_trigger_only: bool
    single_cycle_execution: bool
    permanent_automation_enabled: bool
    max_eligible_sends_per_cycle: int
    confirm_guarded_automation: bool
    blocked: bool
    dry_run: bool
    automation_enabled_before: bool
    automation_enabled_after: bool
    candidates_found: int
    eligible_candidates_found: int
    skipped_candidates: list[dict[str, Any]]
    executed_send: dict[str, Any] | None
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
    monitoring_integrated: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


async def execute_guarded_automation_cycle(
    db: AsyncSession,
    automation_input: GuardedAutomationInput,
    *,
    settings: Settings | None = None,
    adapter_cls: type[FlowSellSendAdapter] = FlowSellSendAdapter,
) -> GuardedAutomationResult:
    manual_result = await execute_manual_scheduler_cycle(
        db,
        ManualCycleInput(
            confirm_manual_cycle=automation_input.confirm_guarded_automation,
            flow_type=automation_input.flow_type,
            max_candidates=automation_input.max_candidates,
            reminder_horizon_hours=automation_input.reminder_horizon_hours,
            channel=automation_input.channel,
        ),
        settings=settings,
        adapter_cls=adapter_cls,
        record_result=False,
    )
    result = _from_manual_result(manual_result, automation_input.confirm_guarded_automation)
    record_manual_cycle_result(result)
    return result


def _from_manual_result(
    result: ManualCycleResult,
    confirm_guarded_automation: bool,
) -> GuardedAutomationResult:
    data = result.to_dict()
    timeline = [
        "guarded_automation_manual_trigger",
        *data["execution_timeline"],
        "guarded_automation_cycle_finished",
    ]
    safety_guards = [
        "guarded automation bridge only",
        "does not enable permanent automation",
        *data["safety_guards"],
    ]
    return GuardedAutomationResult(
        guarded_automation=True,
        manual_trigger_only=True,
        single_cycle_execution=True,
        permanent_automation_enabled=False,
        max_eligible_sends_per_cycle=data["max_eligible_sends_per_cycle"],
        confirm_guarded_automation=confirm_guarded_automation,
        blocked=data["blocked"],
        dry_run=data["dry_run"],
        automation_enabled_before=data["automation_enabled_before"],
        automation_enabled_after=data["automation_enabled_after"],
        candidates_found=data["candidates_found"],
        eligible_candidates_found=data["eligible_candidates_found"],
        skipped_candidates=data["skipped_candidates"],
        executed_send=data["executed_send"],
        execution_summary=(
            "Guarded automation one-shot cycle blocked by safety guards."
            if data["blocked"]
            else "Guarded automation one-shot cycle completed with one controlled send attempt."
        ),
        execution_timeline=timeline,
        safety_guards=safety_guards,
        guard_errors=data["guard_errors"],
        provider_access=data["provider_access"],
        send_adapter_called=data["send_adapter_called"],
        send_pipeline_called=data["send_pipeline_called"],
        background_execution=False,
        cron_execution=False,
        queue_execution=False,
        bulk_execution=False,
        monitoring_integrated=True,
    )
