"""Read-only staging foundation for future scheduler automation.

This module does not start jobs, loops, workers, queues, or sends. It exposes
configuration and safety guards so staging rollout can be inspected before any
automation layer is implemented.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.core.config import Settings, get_settings


@dataclass(frozen=True, slots=True)
class SchedulerStagingStatus:
    foundation_enabled: bool
    staging_mode: bool
    active_execution_enabled: bool
    background_loop_enabled: bool
    max_records_per_cycle: int
    only_test_recipients: bool
    test_recipients_configured: bool
    test_recipient_count: int
    dry_run_required: bool
    flowsell_dry_run: bool
    dry_run_enforced: bool
    safety_guards: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_scheduler_staging_status(settings: Settings | None = None) -> SchedulerStagingStatus:
    current = settings or get_settings()
    test_recipients = current.test_recipient_phones
    dry_run_enforced = (not current.SCHEDULER_STAGING_REQUIRE_DRY_RUN) or current.FLOWSELL_DRY_RUN

    return SchedulerStagingStatus(
        foundation_enabled=current.SCHEDULER_STAGING_FOUNDATION_ENABLED,
        staging_mode=current.SCHEDULER_STAGING_MODE,
        active_execution_enabled=False,
        background_loop_enabled=False,
        max_records_per_cycle=current.SCHEDULER_STAGING_MAX_RECORDS,
        only_test_recipients=current.SCHEDULER_STAGING_ONLY_TEST_RECIPIENTS,
        test_recipients_configured=bool(test_recipients),
        test_recipient_count=len(test_recipients),
        dry_run_required=current.SCHEDULER_STAGING_REQUIRE_DRY_RUN,
        flowsell_dry_run=current.FLOWSELL_DRY_RUN,
        dry_run_enforced=dry_run_enforced,
        safety_guards=(
            "no active scheduler execution",
            "no background infinite loops",
            "max 1 record per cycle",
            "TEST_RECIPIENTS only",
            "FLOWSELL_DRY_RUN required",
            "no queues/workers/retry loops",
            "controlled send adapter remains the only send path",
        ),
    )
