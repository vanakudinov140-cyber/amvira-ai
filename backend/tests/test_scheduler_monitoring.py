import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=import-error
from app.scheduler.execution_preview import SchedulerExecutionPreview
from app.scheduler.manual_cycle import ManualCycleResult
from app.scheduler.monitoring import (
    build_scheduler_monitoring_snapshot,
    clear_monitoring_history,
    get_monitoring_history_summary,
    record_manual_cycle_result,
)


def _manual_cycle_result() -> ManualCycleResult:
    return ManualCycleResult(
        manual_trigger_only=True,
        single_cycle_execution=True,
        max_eligible_sends_per_cycle=1,
        confirm_manual_cycle=True,
        blocked=True,
        dry_run=False,
        automation_enabled_before=False,
        automation_enabled_after=False,
        candidates_found=2,
        eligible_candidates_found=1,
        skipped_candidates=[],
        executed_send=None,
        execution_summary="Manual single-cycle blocked by safety guards.",
        execution_timeline=["manual_cycle_endpoint_invoked", "blocked_before_send_adapter"],
        safety_guards=["manual trigger only"],
        guard_errors=["confirm_manual_cycle=true is required"],
        provider_access=False,
        send_adapter_called=False,
        send_pipeline_called=False,
        background_execution=False,
        cron_execution=False,
        queue_execution=False,
        bulk_execution=False,
    )


def test_monitoring_records_last_manual_cycle_summary() -> None:
    clear_monitoring_history()
    record_manual_cycle_result(_manual_cycle_result())

    history = get_monitoring_history_summary()
    assert history
    assert history[0].blocked is True
    assert history[0].summary == "Manual single-cycle blocked by safety guards."


def test_monitoring_snapshot_is_read_only(monkeypatch) -> None:
    async def fake_preview(*_args, **_kwargs):
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
            candidates_found=0,
            plans=[],
            safety_guards=["manual execution preview only"],
        )

    monkeypatch.setattr("app.scheduler.monitoring.build_scheduler_execution_preview", fake_preview)
    monkeypatch.setattr("app.scheduler.monitoring.scheduler_setup.is_automation_enabled", lambda: False)
    monkeypatch.setattr("app.scheduler.monitoring.scheduler_setup.is_scheduler_running", lambda: False)

    import asyncio

    snapshot = asyncio.run(build_scheduler_monitoring_snapshot(None))  # type: ignore[arg-type]

    assert snapshot.read_only is True
    assert snapshot.automation_enabled is False
    assert snapshot.emergency_stop_active is True
    assert snapshot.background_execution_enabled is False
    assert snapshot.cron_execution_enabled is False
    assert snapshot.queue_execution_enabled is False
    assert snapshot.bulk_execution_enabled is False
    assert "provider/send adapter are not called" in snapshot.safety_guards


def test_monitoring_page_is_human_friendly() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/scheduler/monitoring")
    text = response.text

    assert response.status_code == 200
    assert "Scheduler monitoring" in text
    assert "Только observability" in text
    assert "Без send adapter" in text
    assert "Без provider calls" in text
    assert "/scheduler/monitoring/status" in text
    assert "<pre" not in text.lower()
