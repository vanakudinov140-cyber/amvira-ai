"""Ежедневный retention pipeline (sync → prepare → send)."""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.db.database import AsyncSessionLocal
from app.integrations.flowsell.client import FlowsellClient
from app.integrations.flowsell.service import FlowsellService
from app.integrations.yclients.client import YclientsClient
from app.integrations.yclients.service import YclientsSyncService
from app.scheduler.job_state import mark_job_finished, mark_job_started
from app.services.message_preparation.service import MessagePreparationService
from app.services.messaging.service import MessagingService
from app.services.retention.service import RetentionService

logger = logging.getLogger(__name__)


async def _sync_records() -> int:
    settings = get_settings()
    async with AsyncSessionLocal() as db:
        async with YclientsClient(settings) as yclients:
            sync_service = YclientsSyncService(yclients)
            synced = await sync_service.sync_records(db)
            await db.commit()
            return synced


async def _prepare_messages() -> int:
    preparation = MessagePreparationService(RetentionService(), MessagingService())
    async with AsyncSessionLocal() as db:
        prepared = await preparation.prepare_retention_messages(db)
        await db.commit()
        return prepared


async def _send_pending() -> tuple[int, int]:
    from app.services.messaging.safeguards import is_quiet_hours_active

    settings = get_settings()
    if is_quiet_hours_active(settings=settings):
        logger.info(
            "quiet hours active, skipping send "
            "(quiet_hours_start=%s quiet_hours_end=%s UTC)",
            settings.QUIET_HOURS_START,
            settings.QUIET_HOURS_END,
        )
        return 0, 0

    async with AsyncSessionLocal() as db:
        if settings.TEST_MODE:
            flowsell = FlowsellService(None, settings)
            sent, failed = await flowsell.send_pending_messages(db)
        else:
            async with FlowsellClient(settings) as client:
                flowsell = FlowsellService(client, settings)
                sent, failed = await flowsell.send_pending_messages(db)
        await db.commit()
        return sent, failed


async def run_daily_retention_job(*, force: bool = False) -> None:
    from app.scheduler import job_state

    if not force and not job_state.is_automation_enabled():
        logger.info("RETENTION DAILY JOB SKIPPED — automation disabled")
        return

    mark_job_started()
    errors: list[str] = []

    logger.info("RETENTION DAILY JOB STARTED")

    try:
        synced = await _sync_records()
        logger.info("sync completed: synced=%s records", synced)
    except Exception as exc:
        logger.exception("retention daily job: sync records failed")
        errors.append(f"Синхронизация записей: {exc}")

    try:
        from app.db.database import AsyncSessionLocal
        from app.services.feedback.attribution import ReturnAttributionService

        async with AsyncSessionLocal() as db:
            attributed = await ReturnAttributionService().attribute_returns(db)
            await db.commit()
        logger.info("return attribution: updated=%s", attributed)
    except Exception as exc:
        logger.exception("retention daily job: return attribution failed")
        errors.append(f"Атрибуция возвратов: {exc}")

    try:
        prepared = await _prepare_messages()
        logger.info("messages prepared: count=%s", prepared)
    except Exception as exc:
        logger.exception("retention daily job: prepare messages failed")
        errors.append(f"Подготовка сообщений: {exc}")

    try:
        sent, failed = await _send_pending()
        logger.info("messages sent: sent=%s failed=%s", sent, failed)
    except Exception as exc:
        logger.exception("retention daily job: send pending failed")
        errors.append(f"Отправка очереди: {exc}")

    error_text = "; ".join(errors) if errors else None
    mark_job_finished(success=not errors, error=error_text)
    logger.info(
        "RETENTION DAILY JOB FINISHED status=%s",
        "success" if not errors else "failed",
    )
