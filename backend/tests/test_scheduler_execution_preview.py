import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=import-error,protected-access
from app.core.config import Settings
from app.scheduler.execution_preview import SchedulerCandidateSource, _build_candidate_plan


def _settings(*, dry_run: bool = False) -> Settings:
    return Settings(
        TEST_MODE=True,
        TEST_RECIPIENTS="79990000000",
        FLOWSELL_DRY_RUN=dry_run,
        DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/db",
    )


def test_execution_preview_plan_selects_review_template_without_provider_guard() -> None:
    now = datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc)
    candidate = SchedulerCandidateSource(
        record_id=1,
        yclients_record_id=1001,
        client_id=10,
        client_name="Анна",
        client_phone="79991234567",
        service_name="Стрижка женская",
        appointment_datetime=now - timedelta(days=4),
        master_name=None,
        flow_type="review",
        is_new_client=False,
        candidate_reason="Последний завершённый визит клиента.",
    )

    plan = _build_candidate_plan(candidate, _settings(dry_run=False), now)

    assert plan.matched_category == "haircut"
    assert plan.matched_event == "review_haircut_3d"
    assert plan.selected_template == "review_haircut_template"
    assert plan.delay_rule == {
        "delay_type": "days",
        "delay_value": 3,
        "description": "3 days after completed appointment",
    }
    assert plan.would_send is True
    assert plan.blocked_by_guard is False
    assert plan.provider_access is False
    assert plan.send_adapter_called is False
    assert plan.send_pipeline_called is False
    assert plan.background_execution is False
    assert plan.bulk_execution is False


def test_execution_preview_plan_blocks_candidate_when_delay_not_due() -> None:
    now = datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc)
    candidate = SchedulerCandidateSource(
        record_id=2,
        yclients_record_id=1002,
        client_id=11,
        client_name="Мария",
        client_phone="79991234567",
        service_name="Стрижка женская",
        appointment_datetime=now - timedelta(days=1),
        master_name=None,
        flow_type="review",
        is_new_client=False,
        candidate_reason="Последний завершённый визит клиента.",
    )

    plan = _build_candidate_plan(candidate, _settings(dry_run=False), now)

    assert plan.selected_template == "review_haircut_template"
    assert plan.would_send is False
    assert plan.blocked_by_guard is True
    assert "calculated delay is not due yet" in plan.guard_errors
    assert plan.provider_access is False


def test_execution_preview_page_is_human_friendly() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/scheduler/execution-preview")
    text = response.text

    assert response.status_code == 200
    assert "Preview исполнения scheduler" in text
    assert "Только чтение" in text
    assert "Без реальных отправок" in text
    assert "Без cron/background" in text
    assert "Без queues/workers/retries" in text
    assert "/scheduler/execution-preview" in text
    assert "<pre" not in text.lower()
