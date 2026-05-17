"""In-memory состояние последнего запуска retention scheduler job."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock


@dataclass
class RetentionJobState:
    automation_enabled: bool = True
    last_job_started_at: datetime | None = None
    last_job_finished_at: datetime | None = None
    last_job_status: str | None = None
    last_job_error: str | None = None


_state = RetentionJobState()
_lock = Lock()


def set_automation_enabled(enabled: bool) -> None:
    with _lock:
        _state.automation_enabled = enabled


def is_automation_enabled() -> bool:
    with _lock:
        return _state.automation_enabled


def mark_job_started() -> None:
    with _lock:
        now = datetime.now(timezone.utc)
        _state.last_job_started_at = now
        _state.last_job_finished_at = None
        _state.last_job_status = "running"
        _state.last_job_error = None


def mark_job_finished(*, success: bool, error: str | None = None) -> None:
    with _lock:
        _state.last_job_finished_at = datetime.now(timezone.utc)
        _state.last_job_status = "success" if success else "failed"
        _state.last_job_error = error


def get_job_state() -> RetentionJobState:
    with _lock:
        return RetentionJobState(
            automation_enabled=_state.automation_enabled,
            last_job_started_at=_state.last_job_started_at,
            last_job_finished_at=_state.last_job_finished_at,
            last_job_status=_state.last_job_status,
            last_job_error=_state.last_job_error,
        )
