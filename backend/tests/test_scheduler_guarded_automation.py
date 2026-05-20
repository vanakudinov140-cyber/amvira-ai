import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=import-error
from app.scheduler.guarded_automation import GuardedAutomationInput, execute_guarded_automation_cycle
from app.scheduler.manual_cycle import ManualCycleResult


def _manual_result(*, blocked: bool = False) -> ManualCycleResult:
    return ManualCycleResult(
        manual_trigger_only=True,
        single_cycle_execution=True,
        max_eligible_sends_per_cycle=1,
        confirm_manual_cycle=True,
        blocked=blocked,
        dry_run=False,
        automation_enabled_before=False,
        automation_enabled_after=False,
        candidates_found=2,
        eligible_candidates_found=1,
        skipped_candidates=[],
        executed_send=None,
        execution_summary="Manual single-cycle completed with one controlled send attempt.",
        execution_timeline=[
            "manual_cycle_endpoint_invoked",
            "candidate_selection_completed",
            "send_adapter_execution",
        ],
        safety_guards=[
            "manual trigger only",
            "maximum 1 eligible send per cycle",
            "automation must remain disabled",
            "no background loops/cron execution",
        ],
        guard_errors=[] if not blocked else ["confirm_manual_cycle=true is required"],
        provider_access=not blocked,
        send_adapter_called=not blocked,
        send_pipeline_called=False,
        background_execution=False,
        cron_execution=False,
        queue_execution=False,
        bulk_execution=False,
    )


def test_guarded_automation_wraps_manual_cycle_without_enabling_permanent_automation(monkeypatch) -> None:
    calls: list[object] = []

    async def fake_manual_cycle(*args, **_kwargs):
        calls.append(args[1])
        return _manual_result(blocked=False)

    monkeypatch.setattr("app.scheduler.guarded_automation.execute_manual_scheduler_cycle", fake_manual_cycle)

    result = asyncio.run(
        execute_guarded_automation_cycle(
            None,  # type: ignore[arg-type]
            GuardedAutomationInput(confirm_guarded_automation=True),
        ),
    )

    assert calls
    assert result.guarded_automation is True
    assert result.manual_trigger_only is True
    assert result.single_cycle_execution is True
    assert result.permanent_automation_enabled is False
    assert result.max_eligible_sends_per_cycle == 1
    assert result.automation_enabled_before is False
    assert result.automation_enabled_after is False
    assert result.send_adapter_called is True
    assert result.background_execution is False
    assert result.cron_execution is False
    assert result.queue_execution is False
    assert result.bulk_execution is False
    assert result.monitoring_integrated is True
    assert "guarded_automation_manual_trigger" in result.execution_timeline
    assert "does not enable permanent automation" in result.safety_guards


def test_guarded_automation_page_is_human_friendly() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/scheduler/guarded-automation")
    text = response.text

    assert response.status_code == 200
    assert "Guarded automation one-shot" in text
    assert "Изолированный semi-automation bridge" in text
    assert "TEST_RECIPIENTS only" in text
    assert "No cron/background/queues" in text
    assert "/scheduler/guarded-automation" in text
    assert "<pre" not in text.lower()
