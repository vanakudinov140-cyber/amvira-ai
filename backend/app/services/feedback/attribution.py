"""MVP return attribution: визит в течение N дней после sent_at."""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.client import Client
from app.models.enums import MessageStatus
from app.models.message import Message
from app.models.message_feedback import MessageFeedback
from app.models.record import Record
from app.services.retention import rules

logger = logging.getLogger(__name__)


class ReturnAttributionService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def attribution_window_days(self) -> int:
        return getattr(self._settings, "RETENTION_ATTRIBUTION_DAYS", 30)

    async def attribute_returns(self, db: AsyncSession) -> int:
        window = timedelta(days=self.attribution_window_days)
        stmt = (
            select(Message, Client, MessageFeedback)
            .join(Client, Client.id == Message.client_id)
            .outerjoin(MessageFeedback, MessageFeedback.message_id == Message.id)
            .where(
                Message.status == MessageStatus.sent,
                Message.sent_at.isnot(None),
            )
        )
        rows = (await db.execute(stmt)).all()
        updated = 0

        for message, client, feedback in rows:
            if message.sent_at is None:
                continue

            feedback_row = feedback
            if feedback_row is None:
                feedback_row = MessageFeedback(message_id=message.id)
                db.add(feedback_row)
                await db.flush()

            if feedback_row.client_returned and feedback_row.return_days is not None:
                continue

            window_end = message.sent_at + window
            visit_stmt = (
                select(Record)
                .where(
                    Record.client_id == client.external_id,
                    Record.record_datetime.isnot(None),
                    Record.record_datetime > message.sent_at,
                    Record.record_datetime <= window_end,
                    Record.attendance.in_(rules.COMPLETED_ATTENDANCE_VALUES),
                )
                .order_by(Record.record_datetime.asc())
                .limit(1)
            )
            visit = (await db.execute(visit_stmt)).scalars().first()
            if visit is None or visit.record_datetime is None:
                continue

            return_days = (visit.record_datetime.date() - message.sent_at.date()).days
            revenue = Decimal(str(visit.save_sum or 0))

            feedback_row.client_returned = True
            feedback_row.return_days = max(0, return_days)
            feedback_row.revenue_after_return = revenue
            updated += 1

            logger.info(
                "attribution: message_id=%s client_id=%s return_days=%s revenue=%s",
                message.id,
                message.client_id,
                return_days,
                revenue,
            )

        await db.flush()
        logger.info("attribution: updated %s messages", updated)
        return updated
