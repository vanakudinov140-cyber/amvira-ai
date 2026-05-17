"""APScheduler: ежедневный retention pipeline."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.scheduler import job_state
from app.scheduler.retention_job import run_daily_retention_job

logger = logging.getLogger(__name__)

RETENTION_DAILY_JOB_ID = "retention_daily_pipeline"

_scheduler: AsyncIOScheduler | None = None


def start_retention_scheduler() -> AsyncIOScheduler:
    """Запускает scheduler один раз на процесс (без дублей при reload)."""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.debug("retention scheduler already running, skip start")
        return _scheduler

    settings = get_settings()
    job_state.set_automation_enabled(settings.SCHEDULER_AUTOMATION_ENABLED)

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        run_daily_retention_job,
        trigger=CronTrigger(hour=12, minute=0, timezone="UTC"),
        id=RETENTION_DAILY_JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    if not job_state.is_automation_enabled():
        job = _scheduler.get_job(RETENTION_DAILY_JOB_ID)
        if job is not None:
            job.pause()
    logger.info(
        "Retention scheduler started (automation_enabled=%s)",
        job_state.is_automation_enabled(),
    )
    return _scheduler


def set_automation_enabled(enabled: bool) -> None:
    job_state.set_automation_enabled(enabled)
    scheduler = get_scheduler()
    if scheduler is None:
        return
    job = scheduler.get_job(RETENTION_DAILY_JOB_ID)
    if job is None:
        return
    if enabled:
        job.resume()
        logger.info("Retention automation enabled")
    else:
        job.pause()
        logger.info("Retention automation disabled")


def is_automation_enabled() -> bool:
    return job_state.is_automation_enabled()


async def run_retention_job_now() -> None:
    await run_daily_retention_job(force=True)


def is_scheduler_running() -> bool:
    return _scheduler is not None and _scheduler.running


def get_scheduler() -> AsyncIOScheduler | None:
    return _scheduler


def shutdown_retention_scheduler() -> None:
    global _scheduler

    if _scheduler is None:
        return

    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Retention scheduler stopped")

    _scheduler = None
