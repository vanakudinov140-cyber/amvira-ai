"""Manual dry-run planner for future scheduler automation.

The planner simulates what would be selected for one record. It does not render
templates, call send adapters, access providers, enqueue work, or start jobs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from app.core.config import Settings, get_settings
from app.integrations.flowsell.review_events import (
    REVIEW_EVENT_REGISTRY,
    ReviewEventDefinition,
    match_review_service_category,
)
from app.scheduler.staging_foundation import get_scheduler_staging_status

PlannerFlowType = Literal["reminder", "review"]
ReminderKind = Literal["24h", "2h"]


@dataclass(frozen=True, slots=True)
class PlannerInput:
    flow_type: PlannerFlowType
    service_name: str
    client_phone: str | None = None
    record_id: str | None = None
    is_new_client: bool = False
    reminder_kind: ReminderKind | None = None


@dataclass(frozen=True, slots=True)
class DelayRulePreview:
    delay_type: str
    delay_value: int
    description: str


@dataclass(frozen=True, slots=True)
class SchedulerDryRunPlan:
    dry_run: bool
    would_send: bool
    blocked_by_guard: bool
    matched_flow: str | None
    matched_category: str | None
    matched_event: str | None
    template_id: str | None
    delay_rule: DelayRulePreview | None
    recipient_source: str
    selected_recipient: str | None
    reasons: list[str] = field(default_factory=list)
    guard_errors: list[str] = field(default_factory=list)
    safety_guards: list[str] = field(default_factory=list)
    provider_access: bool = False
    send_pipeline_called: bool = False
    background_execution: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["delay_rule"] = asdict(self.delay_rule) if self.delay_rule else None
        return data


def build_scheduler_dry_run_plan(
    planner_input: PlannerInput,
    *,
    settings: Settings | None = None,
) -> SchedulerDryRunPlan:
    current = settings or get_settings()
    status = get_scheduler_staging_status(current)
    guard_errors = _collect_guard_errors(current)
    recipient = _select_test_recipient(current)
    matched_event: str | None = None
    matched_category: str | None = None
    template_id: str | None = None
    delay_rule: DelayRulePreview | None = None
    reasons: list[str] = []

    if planner_input.flow_type == "reminder":
        reminder_kind = planner_input.reminder_kind or "24h"
        matched_category = "reminder"
        if reminder_kind == "2h":
            matched_event = "reminder_2h"
            template_id = "reminder_2h_template"
            delay_rule = DelayRulePreview("hours_before", 2, "2 hours before appointment")
        else:
            matched_event = "reminder_24h"
            template_id = "reminder_24h_template"
            delay_rule = DelayRulePreview("hours_before", 24, "24 hours before appointment")
        reasons.append(f"manual reminder_kind={reminder_kind} selected")

    elif planner_input.is_new_client:
        definition = _review_definition_for_event("review_new_client_60m")
        matched_category = definition.service_category
        matched_event = definition.event
        template_id = definition.template_id
        delay_rule = DelayRulePreview(
            definition.delay_type,
            definition.delay_value,
            "new client review after first visit",
        )
        reasons.append("is_new_client=true matched new client review flow")

    else:
        category = match_review_service_category(planner_input.service_name)
        if category is None:
            reasons.append("service category was not matched")
        else:
            definition = _review_definition_for_category(category)
            if definition is None:
                reasons.append(f"no review event registered for category={category}")
            else:
                matched_category = definition.service_category
                matched_event = definition.event
                template_id = definition.template_id
                delay_rule = DelayRulePreview(
                    definition.delay_type,
                    definition.delay_value,
                    f"{definition.delay_value} {definition.delay_type} after completed appointment",
                )
                reasons.append(f"service_name matched category={category}")

    if matched_event is None:
        guard_errors.append("no matching flow")

    blocked_by_guard = bool(guard_errors)
    return SchedulerDryRunPlan(
        dry_run=True,
        would_send=not blocked_by_guard,
        blocked_by_guard=blocked_by_guard,
        matched_flow=planner_input.flow_type,
        matched_category=matched_category,
        matched_event=matched_event,
        template_id=template_id,
        delay_rule=delay_rule,
        recipient_source="TEST_RECIPIENTS[0]" if recipient else "none",
        selected_recipient=recipient,
        reasons=reasons,
        guard_errors=guard_errors,
        safety_guards=list(status.safety_guards),
    )


def _collect_guard_errors(settings: Settings) -> list[str]:
    errors: list[str] = []
    if settings.SCHEDULER_STAGING_MAX_RECORDS != 1:
        errors.append("SCHEDULER_STAGING_MAX_RECORDS must be 1")
    if settings.SCHEDULER_STAGING_REQUIRE_DRY_RUN and not settings.FLOWSELL_DRY_RUN:
        errors.append("FLOWSELL_DRY_RUN must be true for scheduler dry-run planner")
    if settings.SCHEDULER_STAGING_ONLY_TEST_RECIPIENTS and not settings.test_recipient_phones:
        errors.append("TEST_RECIPIENTS must contain at least one phone")
    return errors


def _select_test_recipient(settings: Settings) -> str | None:
    return settings.test_recipient_phones[0] if settings.test_recipient_phones else None


def _review_definition_for_event(event: str) -> ReviewEventDefinition:
    for definition in REVIEW_EVENT_REGISTRY:
        if definition.event == event:
            return definition
    raise ValueError(f"Unknown review event: {event}")


def _review_definition_for_category(category: str) -> ReviewEventDefinition | None:
    for definition in REVIEW_EVENT_REGISTRY:
        if definition.service_category == category:
            return definition
    return None
