import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=import-error
from app.core.config import Settings
from app.scheduler.dry_run_planner import PlannerInput, build_scheduler_dry_run_plan


def _settings(*, dry_run: bool = True) -> Settings:
    return Settings(
        TEST_MODE=True,
        TEST_RECIPIENTS="79990000000",
        FLOWSELL_DRY_RUN=dry_run,
        DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/db",
    )


def test_dry_run_planner_matches_new_client_review_flow() -> None:
    plan = build_scheduler_dry_run_plan(
        PlannerInput(
            flow_type="review",
            service_name="Стрижка",
            is_new_client=True,
            client_phone="79991234567",
        ),
        settings=_settings(),
    )

    assert plan.dry_run is True
    assert plan.would_send is True
    assert plan.blocked_by_guard is False
    assert plan.matched_event == "review_new_client_60m"
    assert plan.matched_category == "new_client"
    assert plan.template_id == "review_new_client_60m_template"
    assert plan.delay_rule is not None
    assert plan.delay_rule.delay_type == "minutes"
    assert plan.delay_rule.delay_value == 60
    assert plan.selected_recipient == "79990000000"
    assert plan.provider_access is False
    assert plan.send_pipeline_called is False
    assert plan.background_execution is False


def test_dry_run_planner_matches_service_category_review_flow() -> None:
    plan = build_scheduler_dry_run_plan(
        PlannerInput(flow_type="review", service_name="Сложное окрашивание"),
        settings=_settings(),
    )

    assert plan.matched_category == "coloring"
    assert plan.matched_event == "review_coloring_3d"
    assert plan.template_id == "review_coloring_template"
    assert plan.delay_rule is not None
    assert plan.delay_rule.delay_type == "days"
    assert plan.delay_rule.delay_value == 3


def test_dry_run_planner_matches_reminder_flow() -> None:
    plan = build_scheduler_dry_run_plan(
        PlannerInput(flow_type="reminder", service_name="Стрижка", reminder_kind="2h"),
        settings=_settings(),
    )

    assert plan.matched_event == "reminder_2h"
    assert plan.matched_category == "reminder"
    assert plan.template_id == "reminder_2h_template"
    assert plan.delay_rule is not None
    assert plan.delay_rule.delay_type == "hours_before"
    assert plan.delay_rule.delay_value == 2


def test_dry_run_planner_blocks_when_dry_run_guard_is_disabled() -> None:
    plan = build_scheduler_dry_run_plan(
        PlannerInput(flow_type="review", service_name="Стрижка", is_new_client=True),
        settings=_settings(dry_run=False),
    )

    assert plan.would_send is False
    assert plan.blocked_by_guard is True
    assert any("FLOWSELL_DRY_RUN" in error for error in plan.guard_errors)
    assert plan.provider_access is False
