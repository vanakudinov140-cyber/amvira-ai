import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=import-error
from app.scheduler.delivery_orchestration import (
    OrchestrationPreviewInput,
    build_delivery_orchestration_preview,
)
from app.scheduler.execution_preview import SchedulerExecutionCandidatePlan, SchedulerExecutionPreview


def _eligible_plan() -> SchedulerExecutionCandidatePlan:
    now = datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc)
    return SchedulerExecutionCandidatePlan(
        record_id=1,
        yclients_record_id=1001,
        client_id=10,
        client_name="Анна",
        client_phone="79991234567",
        service_name="Стрижка женская",
        appointment_datetime=(now - timedelta(days=4)).isoformat(),
        flow_type="review",
        candidate_reason="Последний завершённый визит клиента.",
        matched_category="haircut",
        matched_event="review_haircut_3d",
        selected_template="review_haircut_template",
        delay_rule={
            "delay_type": "days",
            "delay_value": 3,
            "description": "3 days after completed appointment",
        },
        scheduled_send_at=(now - timedelta(days=1)).isoformat(),
        would_send=True,
        blocked_by_guard=False,
        execution_reasoning=["delay is due", "Preview stops before send adapter/provider."],
        guard_errors=[],
        planner_reasons=["service_name matched category=haircut"],
    )


def _preview() -> SchedulerExecutionPreview:
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
        candidates_found=1,
        plans=[_eligible_plan()],
        safety_guards=["manual execution preview only"],
    )


def test_orchestration_preview_calculates_max_telegram_whatsapp_chain(monkeypatch) -> None:
    async def fake_execution_preview(*_args, **_kwargs):
        return _preview()

    monkeypatch.setattr(
        "app.scheduler.delivery_orchestration.build_scheduler_execution_preview",
        fake_execution_preview,
    )
    monkeypatch.setattr(
        "app.scheduler.delivery_orchestration.scheduler_setup.is_automation_enabled",
        lambda: False,
    )

    result = asyncio.run(
        build_delivery_orchestration_preview(
            None,  # type: ignore[arg-type]
            OrchestrationPreviewInput(simulate_failed_channel="max"),
        ),
    )

    assert result.read_only is True
    assert result.orchestration_preview_only is True
    assert result.selected_primary_channel == "max"
    assert result.fallback_chain == ["telegram", "whatsapp"]
    assert result.next_fallback_channel == "telegram"
    assert result.would_send_to_max is True
    assert result.would_fallback_to_telegram is True
    assert result.would_fallback_to_whatsapp is True
    assert result.delivery_priority == {"max": 1, "telegram": 2, "whatsapp": 3}
    assert result.escalation_order == ["max", "telegram", "whatsapp"]
    assert result.selected_candidate is not None
    assert result.selected_candidate.selected_template == "review_haircut_template"


def test_orchestration_preview_never_calls_adapters_or_execution_paths(monkeypatch) -> None:
    async def fake_execution_preview(*_args, **_kwargs):
        return _preview()

    monkeypatch.setattr(
        "app.scheduler.delivery_orchestration.build_scheduler_execution_preview",
        fake_execution_preview,
    )
    monkeypatch.setattr(
        "app.scheduler.delivery_orchestration.scheduler_setup.is_automation_enabled",
        lambda: False,
    )

    result = asyncio.run(
        build_delivery_orchestration_preview(
            None,  # type: ignore[arg-type]
            OrchestrationPreviewInput(simulate_failed_channel="telegram"),
        ),
    )

    assert result.provider_access is False
    assert result.send_adapter_called is False
    assert result.send_pipeline_called is False
    assert result.background_execution is False
    assert result.cron_execution is False
    assert result.queue_execution is False
    assert result.bulk_execution is False
    assert result.automation_enabled_before is False
    assert result.automation_enabled_after is False
    assert result.next_fallback_channel == "whatsapp"
    assert result.would_fallback_to_whatsapp is True
    assert "no real fallback sends" in result.safety_guards
    assert "MAX/Telegram/WhatsApp adapters are not instantiated" in result.safety_guards


def test_orchestration_preview_page_is_human_friendly() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/scheduler/orchestration-preview")
    text = response.text

    assert response.status_code == 200
    assert "Delivery orchestration preview" in text
    assert "MAX → Telegram → WhatsApp" in text
    assert "No real fallback sends" in text
    assert "/scheduler/orchestration-preview" in text
    assert "<pre" not in text.lower()
