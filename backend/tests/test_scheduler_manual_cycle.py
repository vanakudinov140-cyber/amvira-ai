import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=import-error
from app.core.config import Settings
from app.integrations.flowsell.send_adapter import FlowSellControlledSendResult
from app.scheduler.execution_preview import SchedulerExecutionCandidatePlan, SchedulerExecutionPreview
from app.scheduler.manual_cycle import ManualCycleInput, execute_manual_scheduler_cycle


def _settings(*, dry_run: bool = False, test_mode: bool = False) -> Settings:
    return Settings(
        TEST_MODE=test_mode,
        TEST_RECIPIENTS="79990000000",
        FLOWSELL_DRY_RUN=dry_run,
        DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/db",
    )


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


def _blocked_plan() -> SchedulerExecutionCandidatePlan:
    plan = _eligible_plan()
    return SchedulerExecutionCandidatePlan(
        **{
            **plan.to_dict(),
            "record_id": 2,
            "yclients_record_id": 1002,
            "would_send": False,
            "blocked_by_guard": True,
            "guard_errors": ["calculated delay is not due yet"],
        },
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
        candidates_found=2,
        plans=[_eligible_plan(), _blocked_plan()],
        safety_guards=["manual execution preview only"],
    )


def test_manual_cycle_requires_confirmation_and_dry_run_disabled(monkeypatch) -> None:
    async def fake_preview(*_args, **_kwargs):
        return _preview()

    monkeypatch.setattr("app.scheduler.manual_cycle.build_scheduler_execution_preview", fake_preview)
    monkeypatch.setattr("app.scheduler.manual_cycle.scheduler_setup.is_automation_enabled", lambda: False)

    result = asyncio.run(
        execute_manual_scheduler_cycle(
            None,  # type: ignore[arg-type]
            ManualCycleInput(confirm_manual_cycle=False),
            settings=_settings(dry_run=True),
        ),
    )

    assert result.blocked is True
    assert result.send_adapter_called is False
    assert result.provider_access is False
    assert any("confirm_manual_cycle" in error for error in result.guard_errors)
    assert any("FLOWSELL_DRY_RUN" in error for error in result.guard_errors)


def test_manual_cycle_sends_only_one_eligible_test_recipient(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    async def fake_preview(*_args, **_kwargs):
        return _preview()

    class FakeAdapter:
        def __init__(self, *, settings: Settings) -> None:
            self._settings = settings

        async def send_event(self, **kwargs: object) -> FlowSellControlledSendResult:
            calls.append(kwargs)
            return FlowSellControlledSendResult(
                dry_run=False,
                sent=True,
                provider="flowsell",
                event=str(kwargs["event"]),
                template="review_haircut_template",
                rendered_text="Анна, добрый день ☀️",
                phone=str(kwargs["phone"]),
                chat_id="79990000000@c.us",
                message_id=None,
                service_type=str(kwargs["service_type"]),
                channel=str(kwargs["channel"]),
                provider_response_preview='{"idMessage":"manual-cycle"}',
            )

    monkeypatch.setattr("app.scheduler.manual_cycle.build_scheduler_execution_preview", fake_preview)
    monkeypatch.setattr("app.scheduler.manual_cycle.scheduler_setup.is_automation_enabled", lambda: False)

    result = asyncio.run(
        execute_manual_scheduler_cycle(
            None,  # type: ignore[arg-type]
            ManualCycleInput(confirm_manual_cycle=True),
            settings=_settings(dry_run=False, test_mode=False),
            adapter_cls=FakeAdapter,  # type: ignore[arg-type]
        ),
    )

    assert result.blocked is False
    assert result.send_adapter_called is True
    assert result.provider_access is True
    assert result.send_pipeline_called is False
    assert result.background_execution is False
    assert result.cron_execution is False
    assert result.bulk_execution is False
    assert len(calls) == 1
    assert calls[0]["phone"] == "79990000000"
    assert calls[0]["event"] == "review_request"
    assert result.executed_send is not None
    assert result.executed_send.selected_template == "review_haircut_template"
    assert result.skipped_candidates


def test_manual_cycle_page_is_human_friendly() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/scheduler/manual-cycle")
    text = response.text

    assert response.status_code == 200
    assert "Manual single-cycle scheduler execution" in text
    assert "Максимум 1 send" in text
    assert "Только TEST_RECIPIENTS" in text
    assert "Без cron/background/queues" in text
    assert "/scheduler/manual-cycle" in text
    assert "<pre" not in text.lower()
