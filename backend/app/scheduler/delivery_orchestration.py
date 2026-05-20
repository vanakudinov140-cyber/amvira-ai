"""Read-only delivery orchestration preview.

The current business delivery priority is MAX -> Telegram -> WhatsApp. This
module calculates that routing and failover reasoning without calling channel
adapters, providers, queues, workers, or background execution paths.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.scheduler import setup as scheduler_setup
from app.scheduler.execution_preview import (
    SchedulerExecutionCandidatePlan,
    SchedulerExecutionPreviewInput,
    build_scheduler_execution_preview,
)

DeliveryChannel = Literal["max", "telegram", "whatsapp"]


class DeliveryAdapter(Protocol):
    """Future adapter contract; previews must not instantiate or call it."""

    channel: DeliveryChannel

    async def send(self, *, recipient: str, message: str) -> object:
        """Send through a concrete channel implementation in a future rollout."""


@dataclass(frozen=True, slots=True)
class DeliveryChannelDefinition:
    channel: DeliveryChannel
    priority: int
    adapter_key: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OrchestrationPreviewInput:
    flow_type: str = "all"
    max_candidates: int = 10
    reminder_horizon_hours: int = 24
    simulate_failed_channel: DeliveryChannel | None = "max"


@dataclass(frozen=True, slots=True)
class OrchestrationCandidatePreview:
    record_id: int
    yclients_record_id: int
    client_name: str
    service_name: str
    flow_type: str
    matched_event: str | None
    selected_template: str | None
    would_send: bool
    blocked_by_guard: bool
    guard_errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DeliveryOrchestrationPreview:
    read_only: bool
    manual_trigger_only: bool
    orchestration_preview_only: bool
    selected_primary_channel: DeliveryChannel
    fallback_chain: list[DeliveryChannel]
    simulated_channel_failure: DeliveryChannel | None
    next_fallback_channel: DeliveryChannel | None
    would_send_to_max: bool
    would_fallback_to_telegram: bool
    would_fallback_to_whatsapp: bool
    delivery_priority: dict[DeliveryChannel, int]
    escalation_order: list[DeliveryChannel]
    why_channel_selected: list[str]
    channel_failover_reasoning: list[str]
    orchestration_reasoning: list[str]
    candidates_found: int
    eligible_candidates_found: int
    selected_candidate: OrchestrationCandidatePreview | None
    safety_guards: list[str] = field(default_factory=list)
    provider_access: bool = False
    send_adapter_called: bool = False
    send_pipeline_called: bool = False
    background_execution: bool = False
    cron_execution: bool = False
    queue_execution: bool = False
    bulk_execution: bool = False
    automation_enabled_before: bool = False
    automation_enabled_after: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["selected_candidate"] = self.selected_candidate.to_dict() if self.selected_candidate else None
        return data


CHANNEL_REGISTRY: tuple[DeliveryChannelDefinition, ...] = (
    DeliveryChannelDefinition(
        channel="max",
        priority=1,
        adapter_key="max",
        description="Primary customer delivery channel.",
    ),
    DeliveryChannelDefinition(
        channel="telegram",
        priority=2,
        adapter_key="telegram",
        description="First fallback channel after MAX failure.",
    ),
    DeliveryChannelDefinition(
        channel="whatsapp",
        priority=3,
        adapter_key="whatsapp",
        description="Second fallback channel after MAX and Telegram failure.",
    ),
)


async def build_delivery_orchestration_preview(
    db: AsyncSession,
    preview_input: OrchestrationPreviewInput,
    *,
    settings: Settings | None = None,
) -> DeliveryOrchestrationPreview:
    automation_enabled_before = scheduler_setup.is_automation_enabled()
    execution_preview = await build_scheduler_execution_preview(
        db,
        SchedulerExecutionPreviewInput(
            flow_type=preview_input.flow_type,  # type: ignore[arg-type]
            max_candidates=preview_input.max_candidates,
            reminder_horizon_hours=preview_input.reminder_horizon_hours,
        ),
        settings=settings,
    )
    eligible = [plan for plan in execution_preview.plans if plan.would_send and not plan.blocked_by_guard]
    selected = eligible[0] if eligible else None
    selected_primary = CHANNEL_REGISTRY[0].channel
    escalation_order = [definition.channel for definition in CHANNEL_REGISTRY]
    fallback_chain = escalation_order[1:]
    next_fallback = _next_fallback(preview_input.simulate_failed_channel, escalation_order)

    return DeliveryOrchestrationPreview(
        read_only=True,
        manual_trigger_only=True,
        orchestration_preview_only=True,
        selected_primary_channel=selected_primary,
        fallback_chain=fallback_chain,
        simulated_channel_failure=preview_input.simulate_failed_channel,
        next_fallback_channel=next_fallback,
        would_send_to_max=selected is not None,
        would_fallback_to_telegram=selected is not None and "telegram" in fallback_chain,
        would_fallback_to_whatsapp=selected is not None and "whatsapp" in fallback_chain,
        delivery_priority={definition.channel: definition.priority for definition in CHANNEL_REGISTRY},
        escalation_order=escalation_order,
        why_channel_selected=_why_channel_selected(selected),
        channel_failover_reasoning=_channel_failover_reasoning(preview_input.simulate_failed_channel, next_fallback),
        orchestration_reasoning=_orchestration_reasoning(selected),
        candidates_found=execution_preview.candidates_found,
        eligible_candidates_found=len(eligible),
        selected_candidate=_candidate_preview(selected) if selected else None,
        safety_guards=[
            "delivery orchestration preview only",
            "provider/send adapters are not called",
            "MAX/Telegram/WhatsApp adapters are not instantiated",
            "no real fallback sends",
            "automation state is not changed",
            "no background execution",
            "no cron execution",
            "no queues/workers/retries",
            "no bulk execution",
            *execution_preview.safety_guards,
        ],
        provider_access=False,
        send_adapter_called=False,
        send_pipeline_called=False,
        background_execution=False,
        cron_execution=False,
        queue_execution=False,
        bulk_execution=False,
        automation_enabled_before=automation_enabled_before,
        automation_enabled_after=scheduler_setup.is_automation_enabled(),
    )


def _next_fallback(
    failed_channel: DeliveryChannel | None,
    escalation_order: list[DeliveryChannel],
) -> DeliveryChannel | None:
    if failed_channel is None or failed_channel not in escalation_order:
        return None
    failed_index = escalation_order.index(failed_channel)
    if failed_index + 1 >= len(escalation_order):
        return None
    return escalation_order[failed_index + 1]


def _why_channel_selected(selected: SchedulerExecutionCandidatePlan | None) -> list[str]:
    reasons = [
        "business priority selects MAX as the primary delivery channel",
        "Telegram is reserved as first fallback",
        "WhatsApp is reserved as fallback channel, not primary",
    ]
    if selected is None:
        reasons.append("no eligible scheduler candidate selected for delivery simulation")
    else:
        reasons.append(
            f"eligible scheduler candidate selected: record={selected.yclients_record_id}, "
            f"template={selected.selected_template or 'not selected'}",
        )
    return reasons


def _channel_failover_reasoning(
    failed_channel: DeliveryChannel | None,
    next_fallback: DeliveryChannel | None,
) -> list[str]:
    if failed_channel is None:
        return ["no channel failure simulated; primary MAX remains selected"]
    if next_fallback is None:
        return [f"{failed_channel} failure simulated; no further fallback channel is available"]
    return [
        f"{failed_channel} failure simulated",
        f"next fallback channel would be {next_fallback}",
        "fallback is calculated only; no fallback send is executed",
    ]


def _orchestration_reasoning(selected: SchedulerExecutionCandidatePlan | None) -> list[str]:
    reasoning = [
        "scheduler execution preview selected eligible candidates without provider access",
        "delivery orchestration applied business priority MAX -> Telegram -> WhatsApp",
        "adapter boundary is represented by DeliveryAdapter protocol for future safe rollout",
        "preview stops before any channel adapter or provider call",
    ]
    if selected is None:
        reasoning.append("no message would be sent because there is no eligible scheduler candidate")
    else:
        reasoning.append("one eligible message would start on MAX before any fallback consideration")
    return reasoning


def _candidate_preview(plan: SchedulerExecutionCandidatePlan) -> OrchestrationCandidatePreview:
    return OrchestrationCandidatePreview(
        record_id=plan.record_id,
        yclients_record_id=plan.yclients_record_id,
        client_name=plan.client_name,
        service_name=plan.service_name,
        flow_type=plan.flow_type,
        matched_event=plan.matched_event,
        selected_template=plan.selected_template,
        would_send=plan.would_send,
        blocked_by_guard=plan.blocked_by_guard,
        guard_errors=plan.guard_errors,
    )
