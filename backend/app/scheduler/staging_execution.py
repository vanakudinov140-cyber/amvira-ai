"""Manual one-record staging execution preview.

This module intentionally stops before provider access. It runs planner
selection, template rendering, and payload preview building for one record only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.config import Settings, get_settings
from app.integrations.flowsell.client import FlowsellClient
from app.integrations.flowsell.exceptions import FlowsellNotConfiguredError
from app.integrations.flowsell.send_adapter import FlowSellSendAdapter
from app.integrations.flowsell.mapper import (
    map_retention_channel_to_delivery,
    phone_to_chat_id,
    retention_channel_supported,
)
from app.integrations.flowsell.templates import load_template_catalog
from app.integrations.flowsell.templates.renderer import render_text
from app.scheduler.dry_run_planner import PlannerInput, SchedulerDryRunPlan, build_scheduler_dry_run_plan

MAX_FLOWSELL_TEXT_LENGTH = 4096


@dataclass(frozen=True, slots=True)
class StagingExecutionInput:
    flow_type: str
    service_name: str
    client_phone: str | None = None
    record_id: str | None = None
    is_new_client: bool = False
    reminder_kind: str | None = None
    client_name: str = "Клиент"
    appointment_date: str = "дата визита"
    appointment_time: str = "время визита"
    master_name: str = "мастер"
    booking_link: str = "https://example.com/booking-preview"
    channel: str = "sms"


@dataclass(frozen=True, slots=True)
class StagingRealSendInput(StagingExecutionInput):
    confirm_real_send: bool = False


@dataclass(frozen=True, slots=True)
class StagingSendPayloadPreview:
    event: str
    template: str
    phone: str
    channel: str
    delivery_channel: str
    chat_id: str | None
    valid: bool
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)
    missing_placeholders: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SimulatedWhatsAppPayload:
    chat_id: str | None
    message: str
    channel: str
    provider: str = "flowsell"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StagingExecutionPreview:
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
    simulated_whatsapp_payload: SimulatedWhatsAppPayload | None = None
    normalized_chat_id: str | None = None
    template_used: str | None = None
    render_status: str = "not_rendered"
    payload_validation_status: str = "not_validated"
    would_be_sent: bool = False
    provider_block_reason: str = "not_reached"
    final_dry_run_stop_stage: str = "blocked_before_payload_build"
    execution_timeline: list[str] = field(default_factory=list)
    send_payload_preview: StagingSendPayloadPreview | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["simulated_whatsapp_payload"] = (
            self.simulated_whatsapp_payload.to_dict() if self.simulated_whatsapp_payload else None
        )
        data["send_payload_preview"] = (
            self.send_payload_preview.to_dict() if self.send_payload_preview else None
        )
        return data


@dataclass(frozen=True, slots=True)
class StagingRealSendResult:
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
    provider_diagnostics: "StagingProviderDiagnostics | None"
    send_adapter_called: bool
    provider_access: bool
    background_execution: bool
    bulk_execution: bool

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["provider_diagnostics"] = (
            self.provider_diagnostics.to_dict() if self.provider_diagnostics else None
        )
        return data


@dataclass(frozen=True, slots=True)
class StagingProviderDiagnostics:
    provider_accepted: bool
    connection_state: str
    whatsapp_session_state: str
    qr_login_required: bool | None
    test_recipient_whatsapp: str
    delivery_status: str
    delivery_status_available: bool
    provider_delivery_state: str
    possible_failure_reason: str | None
    diagnostics_errors: list[str] = field(default_factory=list)
    account_wid: str | int | None = None
    webhook_configured: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_staging_execution_preview(
    execution_input: StagingExecutionInput,
    *,
    settings: Settings | None = None,
) -> StagingExecutionPreview:
    current = settings or get_settings()
    steps = ["manual_endpoint_invoked", "single_record_guard"]
    plan = build_scheduler_dry_run_plan(
        PlannerInput(
            flow_type=execution_input.flow_type,  # type: ignore[arg-type]
            service_name=execution_input.service_name,
            client_phone=execution_input.client_phone,
            record_id=execution_input.record_id,
            is_new_client=execution_input.is_new_client,
            reminder_kind=execution_input.reminder_kind,  # type: ignore[arg-type]
        ),
        settings=current,
    )
    steps.append("planner_selection")

    if plan.matched_category:
        steps.append("category_matching")
    if plan.template_id:
        steps.append("template_selection")

    guard_errors = list(plan.guard_errors)
    if not current.FLOWSELL_DRY_RUN and "FLOWSELL_DRY_RUN must be true for staging execution" not in guard_errors:
        guard_errors.append("FLOWSELL_DRY_RUN must be true for staging execution")

    if guard_errors or not plan.matched_event or not plan.template_id or not plan.selected_recipient:
        steps.append("blocked_before_payload_build")
        return _blocked_result(
            plan=plan,
            execution_input=execution_input,
            steps=steps,
            guard_errors=guard_errors,
            dry_run=current.FLOWSELL_DRY_RUN,
        )

    values = _template_values(execution_input)
    steps.append("payload_preparation")
    payload_preview, rendered_text = _build_payload_preview(
        plan=plan,
        recipient=plan.selected_recipient,
        values=values,
        channel=execution_input.channel,
    )
    steps.extend(["template_rendering", "send_payload_build", "provider_blocked"])
    would_be_sent = payload_preview.valid and not guard_errors
    render_status = "rendered" if rendered_text else "render_failed"
    payload_validation_status = "valid" if payload_preview.valid else "invalid"

    return StagingExecutionPreview(
        dry_run=True,
        dry_run_confirmed=current.FLOWSELL_DRY_RUN,
        provider_blocked=True,
        provider_access=False,
        send_adapter_called=False,
        send_pipeline_called=False,
        background_execution=False,
        matched_flow=plan.matched_flow,
        matched_category=plan.matched_category,
        matched_event=plan.matched_event,
        template_id=plan.template_id,
        rendered_text_preview=rendered_text,
        recipient_used=plan.selected_recipient,
        record_id=execution_input.record_id,
        execution_steps_completed=steps,
        guard_errors=guard_errors,
        safety_guards=plan.safety_guards,
        validation_errors=payload_preview.validation_errors,
        validation_warnings=payload_preview.validation_warnings,
        simulated_whatsapp_payload=SimulatedWhatsAppPayload(
            chat_id=payload_preview.chat_id,
            message=rendered_text,
            channel=payload_preview.delivery_channel,
        ),
        normalized_chat_id=payload_preview.chat_id,
        template_used=payload_preview.template,
        render_status=render_status,
        payload_validation_status=payload_validation_status,
        would_be_sent=would_be_sent,
        provider_block_reason="flowsell_dry_run_enabled",
        final_dry_run_stop_stage="dry_run_provider_block",
        execution_timeline=[
            "scenario_matched",
            "template_selected",
            "text_rendered",
            "payload_prepared",
            "checks_passed" if payload_preview.valid else "checks_failed",
            "send_blocked_by_dry_run",
        ],
        send_payload_preview=payload_preview,
    )


def _blocked_result(
    *,
    plan: SchedulerDryRunPlan,
    execution_input: StagingExecutionInput,
    steps: list[str],
    guard_errors: list[str],
    dry_run: bool,
) -> StagingExecutionPreview:
    return StagingExecutionPreview(
        dry_run=dry_run,
        dry_run_confirmed=False,
        provider_blocked=True,
        provider_access=False,
        send_adapter_called=False,
        send_pipeline_called=False,
        background_execution=False,
        matched_flow=plan.matched_flow,
        matched_category=plan.matched_category,
        matched_event=plan.matched_event,
        template_id=plan.template_id,
        rendered_text_preview=None,
        recipient_used=plan.selected_recipient,
        record_id=execution_input.record_id,
        execution_steps_completed=steps,
        guard_errors=guard_errors,
        safety_guards=plan.safety_guards,
        validation_errors=[],
        validation_warnings=[],
        provider_block_reason="safety_guard_before_provider",
        execution_timeline=[
            "scenario_matched" if plan.matched_event else "scenario_not_matched",
            "template_selected" if plan.template_id else "template_not_selected",
            "blocked_before_payload_build",
        ],
        send_payload_preview=None,
    )


def _build_payload_preview(
    *,
    plan: SchedulerDryRunPlan,
    recipient: str,
    values: dict[str, object | None],
    channel: str,
) -> tuple[StagingSendPayloadPreview, str]:
    catalog = load_template_catalog()
    template = catalog.get(plan.template_id or "")
    rendered_text, missing = render_text(template.text, values)
    text = rendered_text.strip()
    validation_errors: list[str] = []
    validation_warnings = [f"missing placeholder fallback used: {name}" for name in missing]
    chat_id: str | None = None

    if not retention_channel_supported(channel):
        validation_errors.append(f"unsupported channel: {channel}")
    try:
        chat_id = phone_to_chat_id(recipient)
    except ValueError as exc:
        validation_errors.append(str(exc))
    if not text:
        validation_errors.append("rendered_text is empty")
    if len(text) > MAX_FLOWSELL_TEXT_LENGTH:
        validation_errors.append(f"rendered_text too long: {len(text)} > {MAX_FLOWSELL_TEXT_LENGTH}")
    if not plan.matched_event:
        validation_errors.append("event is required")
    if not recipient.strip():
        validation_errors.append("phone is required")

    return (
        StagingSendPayloadPreview(
            event=plan.matched_event or "",
            template=template.id,
            phone=recipient,
            channel=channel,
            delivery_channel=map_retention_channel_to_delivery(channel),
            chat_id=chat_id,
            valid=not validation_errors,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            missing_placeholders=list(missing),
        ),
        text,
    )


def _template_values(execution_input: StagingExecutionInput) -> dict[str, object | None]:
    return {
        "client_name": execution_input.client_name,
        "service_name": execution_input.service_name,
        "appointment_date": execution_input.appointment_date,
        "appointment_time": execution_input.appointment_time,
        "master_name": execution_input.master_name,
        "booking_link": execution_input.booking_link,
    }


async def execute_staging_real_send_test(
    execution_input: StagingRealSendInput,
    *,
    settings: Settings | None = None,
) -> StagingRealSendResult:
    current = settings or get_settings()
    safety_checks = [
        "manual trigger only",
        "single message execution only",
        "TEST_RECIPIENTS[0] recipient only",
        "FLOWSELL_DRY_RUN=false required",
        "no scheduler/background execution",
        "no queues/workers/retries",
    ]
    guard_errors: list[str] = []
    timeline = ["manual_endpoint_invoked", "single_message_guard"]

    if not execution_input.confirm_real_send:
        guard_errors.append("confirm_real_send=true is required")
    if current.FLOWSELL_DRY_RUN:
        guard_errors.append("FLOWSELL_DRY_RUN must be false for staging real send test")
    if current.SCHEDULER_STAGING_MAX_RECORDS != 1:
        guard_errors.append("SCHEDULER_STAGING_MAX_RECORDS must be 1")

    recipient = current.test_recipient_phones[0] if current.test_recipient_phones else None
    if recipient is None:
        guard_errors.append("TEST_RECIPIENTS must contain at least one phone")
    elif recipient not in current.test_recipient_phones:
        guard_errors.append("recipient must be selected from TEST_RECIPIENTS")

    planner_settings = current.model_copy(update={"FLOWSELL_DRY_RUN": True})
    plan = build_scheduler_dry_run_plan(
        PlannerInput(
            flow_type=execution_input.flow_type,  # type: ignore[arg-type]
            service_name=execution_input.service_name,
            client_phone=execution_input.client_phone,
            record_id=execution_input.record_id,
            is_new_client=execution_input.is_new_client,
            reminder_kind=execution_input.reminder_kind,  # type: ignore[arg-type]
        ),
        settings=planner_settings,
    )
    timeline.extend(["planner_selection", "category_matching", "template_selection"])

    if not plan.matched_event:
        guard_errors.append("matching flow is required")
    if not plan.template_id:
        guard_errors.append("template_id is required")
    if plan.guard_errors:
        guard_errors.extend(plan.guard_errors)

    adapter_event: str | None = None
    if plan.template_id:
        adapter_event = load_template_catalog().get(plan.template_id).event

    if guard_errors:
        return _blocked_real_send_result(
            execution_input=execution_input,
            plan=plan,
            adapter_event=adapter_event,
            recipient=recipient,
            timeline=timeline + ["blocked_before_send_adapter"],
            safety_checks=safety_checks,
            guard_errors=guard_errors,
            dry_run=current.FLOWSELL_DRY_RUN,
        )

    values = _template_values(execution_input)
    timeline.extend(["template_rendering", "payload_validation", "send_adapter_execution"])
    result = await FlowSellSendAdapter(settings=current).send_event(
        event=adapter_event or plan.matched_event or "",
        phone=recipient or "",
        values=values,
        service_type=plan.matched_category,
        channel=execution_input.channel,
    )
    timeline.append("provider_response_received" if result.provider_response_preview else "adapter_result_received")
    diagnostics = await _build_provider_diagnostics(
        settings=current,
        recipient=result.phone,
        chat_id=result.chat_id,
        message_id=result.message_id,
    )

    return StagingRealSendResult(
        manual_trigger_only=True,
        single_message_execution=True,
        confirm_real_send=execution_input.confirm_real_send,
        blocked=False,
        sent=result.sent,
        dry_run=result.dry_run,
        matched_category=plan.matched_category,
        matched_event=plan.matched_event,
        template_id=plan.template_id,
        adapter_event=adapter_event,
        rendered_text=result.rendered_text,
        recipient_used=result.phone,
        chat_id=result.chat_id,
        message_id=result.message_id,
        provider=result.provider,
        provider_response_preview=result.provider_response_preview,
        execution_timeline=timeline,
        safety_checks=safety_checks,
        guard_errors=[],
        validation_errors=result.validation_errors,
        warnings=result.warnings,
        provider_diagnostics=diagnostics,
        send_adapter_called=True,
        provider_access=bool(result.provider_response_preview or result.message_id),
        background_execution=False,
        bulk_execution=False,
    )


async def build_staging_provider_diagnostics(
    *,
    message_id: str,
    settings: Settings | None = None,
) -> StagingProviderDiagnostics:
    current = settings or get_settings()
    recipient = current.test_recipient_phones[0] if current.test_recipient_phones else ""
    return await _build_provider_diagnostics(
        settings=current,
        recipient=recipient,
        chat_id=_safe_chat_id(recipient),
        message_id=message_id.strip() or None,
    )


def _blocked_real_send_result(
    *,
    execution_input: StagingRealSendInput,
    plan: SchedulerDryRunPlan,
    adapter_event: str | None,
    recipient: str | None,
    timeline: list[str],
    safety_checks: list[str],
    guard_errors: list[str],
    dry_run: bool,
) -> StagingRealSendResult:
    return StagingRealSendResult(
        manual_trigger_only=True,
        single_message_execution=True,
        confirm_real_send=execution_input.confirm_real_send,
        blocked=True,
        sent=False,
        dry_run=dry_run,
        matched_category=plan.matched_category,
        matched_event=plan.matched_event,
        template_id=plan.template_id,
        adapter_event=adapter_event,
        rendered_text=None,
        recipient_used=recipient,
        chat_id=_safe_chat_id(recipient),
        message_id=None,
        provider="flowsell",
        provider_response_preview=None,
        execution_timeline=timeline,
        safety_checks=safety_checks,
        guard_errors=guard_errors,
        validation_errors=[],
        warnings=[],
        provider_diagnostics=None,
        send_adapter_called=False,
        provider_access=False,
        background_execution=False,
        bulk_execution=False,
    )


def _safe_chat_id(phone: str | None) -> str | None:
    if not phone:
        return None
    try:
        return phone_to_chat_id(phone)
    except ValueError:
        return None


async def _build_provider_diagnostics(
    *,
    settings: Settings,
    recipient: str,
    chat_id: str | None,
    message_id: str | None,
) -> StagingProviderDiagnostics:
    errors: list[str] = []
    account_wid: str | int | None = None
    webhook_configured: bool | None = None
    connection_state = "not_checked"
    whatsapp_session_state = "not_checked"
    qr_login_required: bool | None = None
    test_recipient_whatsapp = "not_checked"
    delivery_status = "not_checked"
    delivery_status_available = False
    provider_delivery_state = "accepted" if message_id else "not_accepted"

    try:
        async with FlowsellClient(settings) as client:
            settings_result = await client.get_account_settings()
            if settings_result.ok:
                connection_state = "settings_available"
                account_wid = (settings_result.data or {}).get("wid")
                webhook_configured = bool((settings_result.data or {}).get("webhookUrl"))
            else:
                connection_state = "settings_unavailable"
                errors.append(f"getSettings: {settings_result.detail}")

            qr_result = await client.get_qr_status()
            if qr_result.ok:
                qr_type = str((qr_result.data or {}).get("type") or "")
                if qr_type == "alreadyLogged":
                    whatsapp_session_state = "authorized"
                    qr_login_required = False
                elif qr_type == "qrCode":
                    whatsapp_session_state = "qr_login_required"
                    qr_login_required = True
                elif qr_type == "error":
                    whatsapp_session_state = "qr_error"
                    qr_login_required = None
                    errors.append(f"qr: {(qr_result.data or {}).get('message')}")
                else:
                    whatsapp_session_state = qr_type or "unknown"
                    qr_login_required = None
            else:
                whatsapp_session_state = "qr_status_unavailable"
                errors.append(f"qr: {qr_result.detail}")

            whatsapp_result = await client.check_whatsapp(recipient)
            test_recipient_whatsapp = "exists" if whatsapp_result.ok else "not_found_or_unavailable"
            if not whatsapp_result.ok:
                errors.append(f"checkWhatsapp: {whatsapp_result.detail}")

            if chat_id and message_id:
                message_result = await client.get_message_status(chat_id=chat_id, id_message=message_id)
                if message_result.ok:
                    delivery_status_available = True
                    delivery_status = message_result.detail
                    provider_delivery_state = delivery_status
                else:
                    delivery_status = "unavailable"
                    errors.append(f"getMessage: {message_result.detail}")
    except FlowsellNotConfiguredError as exc:
        connection_state = "not_configured"
        whatsapp_session_state = "not_configured"
        test_recipient_whatsapp = "not_checked"
        delivery_status = "unavailable"
        errors.append(str(exc))

    possible_failure_reason = _diagnostic_failure_reason(
        whatsapp_session_state=whatsapp_session_state,
        test_recipient_whatsapp=test_recipient_whatsapp,
        delivery_status=delivery_status,
        delivery_status_available=delivery_status_available,
        diagnostics_errors=errors,
    )
    return StagingProviderDiagnostics(
        provider_accepted=bool(message_id),
        connection_state=connection_state,
        whatsapp_session_state=whatsapp_session_state,
        qr_login_required=qr_login_required,
        test_recipient_whatsapp=test_recipient_whatsapp,
        delivery_status=delivery_status,
        delivery_status_available=delivery_status_available,
        provider_delivery_state=provider_delivery_state,
        possible_failure_reason=possible_failure_reason,
        diagnostics_errors=errors,
        account_wid=account_wid,
        webhook_configured=webhook_configured,
    )


def _diagnostic_failure_reason(
    *,
    whatsapp_session_state: str,
    test_recipient_whatsapp: str,
    delivery_status: str,
    delivery_status_available: bool,
    diagnostics_errors: list[str],
) -> str | None:
    if whatsapp_session_state == "qr_login_required":
        return "WhatsApp session requires QR login"
    if whatsapp_session_state not in {"authorized", "not_checked"} and "unavailable" not in whatsapp_session_state:
        return f"WhatsApp session state: {whatsapp_session_state}"
    if test_recipient_whatsapp == "not_found_or_unavailable":
        return "TEST_RECIPIENTS[0] may not have WhatsApp or checkWhatsapp is unavailable"
    if delivery_status in {"failed", "noAccount", "notInGroup", "yellowCard"}:
        return f"Provider delivery status: {delivery_status}"
    if delivery_status in {"pending", "sent"}:
        return f"Provider accepted message, delivery is still {delivery_status}"
    if not delivery_status_available and diagnostics_errors:
        return "Provider accepted message, but delivery status lookup is unavailable"
    return None
