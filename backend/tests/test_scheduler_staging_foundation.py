import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=import-error
from app.core.config import Settings
from app.scheduler.staging_foundation import get_scheduler_staging_status


def test_scheduler_staging_foundation_is_non_executing_by_default() -> None:
    settings = Settings(
        TEST_MODE=True,
        TEST_RECIPIENTS="79990000000",
        FLOWSELL_DRY_RUN=True,
        DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/db",
    )

    status = get_scheduler_staging_status(settings)

    assert status.foundation_enabled is False
    assert status.staging_mode is True
    assert status.active_execution_enabled is False
    assert status.background_loop_enabled is False
    assert status.max_records_per_cycle == 1
    assert status.only_test_recipients is True
    assert status.dry_run_required is True
    assert status.flowsell_dry_run is True
    assert status.dry_run_enforced is True


def test_scheduler_staging_foundation_reports_missing_dry_run_guard() -> None:
    settings = Settings(
        TEST_MODE=True,
        TEST_RECIPIENTS="79990000000",
        FLOWSELL_DRY_RUN=False,
        DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/db",
    )

    status = get_scheduler_staging_status(settings)

    assert status.dry_run_required is True
    assert status.flowsell_dry_run is False
    assert status.dry_run_enforced is False
    assert status.active_execution_enabled is False


def test_scheduler_staging_max_records_is_hard_limited() -> None:
    try:
        Settings(
            TEST_MODE=True,
            TEST_RECIPIENTS="79990000000",
            FLOWSELL_DRY_RUN=True,
            SCHEDULER_STAGING_MAX_RECORDS=2,
            DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/db",
        )
    except ValueError as exc:
        assert "SCHEDULER_STAGING_MAX_RECORDS" in str(exc)
    else:
        raise AssertionError("SCHEDULER_STAGING_MAX_RECORDS must reject values above 1")


def test_scheduler_dry_run_preview_endpoint_is_simulation_only() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/scheduler/dry-run-preview",
        json={
            "flow_type": "review",
            "service_name": "Окрашивание волос",
            "is_new_client": False,
            "client_phone": "79991234567",
        },
    )
    data = response.json()

    assert response.status_code == 200
    assert data["dry_run"] is True
    assert data["matched_event"] == "review_coloring_3d"
    assert data["template_id"] == "review_coloring_template"
    assert data["provider_access"] is False
    assert data["send_pipeline_called"] is False
    assert data["background_execution"] is False


def test_scheduler_planner_preview_page_is_human_friendly() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/scheduler/planner-preview")
    text = response.text

    assert response.status_code == 200
    assert "Проверка логики планировщика" in text
    assert "DRY RUN ONLY" in text
    assert "NO REAL SENDS" in text
    assert "PROVIDER DISABLED" in text
    assert "/scheduler/dry-run-preview" in text
