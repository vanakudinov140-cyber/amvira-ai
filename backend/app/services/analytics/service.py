"""Read-only analytics (SQLAlchemy, без внешних API)."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.client import Client
from app.models.enums import MessageStatus
from app.models.message import Message
from app.models.procedure import Procedure
from app.models.record import Record
from app.scheduler.job_state import get_job_state
from app.scheduler.setup import is_scheduler_running
from app.services.messaging.safeguards import count_daily_sent
from app.services.retention import rules
from app.services.retention.rules import RetentionAction
from app.services.retention.service import RetentionService

logger = logging.getLogger(__name__)

_ACTION_KEYS: tuple[RetentionAction, ...] = (
    "monthly_care",
    "gentle_return",
    "comeback_reminder",
    "winback",
)


class AnalyticsService:
    def __init__(
        self,
        retention: RetentionService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._retention = retention or RetentionService()
        self._settings = settings or get_settings()

    async def get_retention_overview(self, db: AsyncSession) -> dict[str, object]:
        logger.info("analytics: calculating retention-overview")

        clients_total = await db.scalar(select(func.count()).select_from(Client)) or 0
        logger.info("analytics: clients_total=%s", clients_total)

        candidates = await self._retention.get_retention_candidates(db)
        retention_candidates = len(candidates)
        logger.info("analytics: retention_candidates=%s", retention_candidates)

        actions_counter: Counter[str] = Counter()
        for candidate in candidates:
            actions_counter[candidate.recommended_action] += 1

        messages_pending = await self._count_messages(db, MessageStatus.pending)
        messages_approved = await self._count_messages(db, MessageStatus.approved)
        messages_rejected = await self._count_messages(db, MessageStatus.rejected)
        messages_sent = await self._count_messages(db, MessageStatus.sent)
        messages_failed = await self._count_messages(db, MessageStatus.failed)
        daily_sent = await count_daily_sent(db, self._settings)

        actions_breakdown = {
            action: int(actions_counter.get(action, 0)) for action in _ACTION_KEYS
        }

        logger.info(
            "analytics: retention-overview messages pending=%s approved=%s rejected=%s "
            "sent=%s failed=%s daily_sent=%s actions=%s",
            messages_pending,
            messages_approved,
            messages_rejected,
            messages_sent,
            messages_failed,
            daily_sent,
            actions_breakdown,
        )

        return {
            "clients_total": int(clients_total),
            "retention_candidates": retention_candidates,
            "messages_pending": messages_pending,
            "messages_approved": messages_approved,
            "messages_rejected": messages_rejected,
            "messages_sent": messages_sent,
            "messages_failed": messages_failed,
            "daily_sent": daily_sent,
            "actions_breakdown": actions_breakdown,
        }

    async def get_message_performance(self, db: AsyncSession) -> dict[str, object]:
        logger.info("analytics: calculating message-performance")

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        prepared_last_24h = await self._count_messages_since(
            db,
            cutoff,
            statuses=(
                MessageStatus.pending,
                MessageStatus.approved,
                MessageStatus.rejected,
                MessageStatus.sent,
                MessageStatus.failed,
            ),
        )
        sent_last_24h = await self._count_messages_since(
            db,
            cutoff,
            statuses=(MessageStatus.sent,),
            timestamp_column=Message.sent_at,
        )
        failed_last_24h = await self._count_messages_since(
            db,
            cutoff,
            statuses=(MessageStatus.failed,),
        )

        top_procedures = await self._top_procedures_for_messages_since(db, cutoff)

        logger.info(
            "analytics: message-performance prepared_24h=%s sent_24h=%s failed_24h=%s "
            "top_procedures_count=%s",
            prepared_last_24h,
            sent_last_24h,
            failed_last_24h,
            len(top_procedures),
        )

        return {
            "prepared_last_24h": prepared_last_24h,
            "sent_last_24h": sent_last_24h,
            "failed_last_24h": failed_last_24h,
            "top_procedures": top_procedures,
        }

    def get_scheduler_status(self) -> dict[str, object]:
        logger.info("analytics: calculating scheduler-status")

        state = get_job_state()
        payload = {
            "scheduler_running": is_scheduler_running(),
            "last_job_started_at": state.last_job_started_at,
            "last_job_finished_at": state.last_job_finished_at,
            "last_job_status": state.last_job_status,
            "last_job_error": state.last_job_error,
        }
        logger.info("analytics: scheduler-status %s", payload)
        return payload

    def get_automation_settings(self) -> dict[str, object]:
        from app.scheduler import job_state
        from app.scheduler.setup import is_scheduler_running

        settings = self._settings
        state = get_job_state()
        return {
            "scheduler_running": is_scheduler_running(),
            "automation_enabled": job_state.is_automation_enabled(),
            "test_mode": settings.TEST_MODE,
            "test_recipients": settings.test_recipient_phones,
            "send_pending_limit": settings.SEND_PENDING_LIMIT,
            "daily_send_limit": settings.DAILY_SEND_LIMIT,
            "quiet_hours_start": settings.QUIET_HOURS_START,
            "quiet_hours_end": settings.QUIET_HOURS_END,
            "last_job_started_at": state.last_job_started_at,
            "last_job_finished_at": state.last_job_finished_at,
            "last_job_status": state.last_job_status,
            "last_job_error": state.last_job_error,
        }

    async def get_moderation_insights(self, db: AsyncSession) -> dict[str, object]:
        logger.info("analytics: calculating moderation-insights")

        rows = (
            await db.execute(
                select(Message.status, Message.action, Message.message_metadata),
            )
        ).all()

        segment_counter: Counter[str] = Counter()
        segment_sent: Counter[str] = Counter()
        segment_total: Counter[str] = Counter()
        action_sent: Counter[str] = Counter()
        action_total: Counter[str] = Counter()
        approved = 0
        rejected = 0

        for status, action, metadata in rows:
            segment = "unknown"
            if isinstance(metadata, dict):
                segment = str(metadata.get("client_segment") or "unknown")

            segment_total[segment] += 1
            action_total[action] += 1

            if status == MessageStatus.approved:
                approved += 1
            if status == MessageStatus.rejected:
                rejected += 1
            if status == MessageStatus.sent:
                segment_sent[segment] += 1
                action_sent[action] += 1

        messages_by_segment = dict(segment_total)
        return_rate_by_segment = {
            seg: round(segment_sent[seg] / count, 2) if count else 0.0
            for seg, count in segment_total.items()
        }
        top_performing_actions = [
            {"action": action, "sent": int(action_sent[action]), "total": int(action_total[action])}
            for action, _ in action_sent.most_common()
        ]
        if not top_performing_actions:
            top_performing_actions = [
                {"action": action, "sent": 0, "total": int(action_total[action])}
                for action, _ in action_total.most_common(5)
            ]

        return {
            "messages_by_segment": messages_by_segment,
            "return_rate_by_segment": return_rate_by_segment,
            "top_performing_actions": top_performing_actions[:10],
            "ai_moderation": {
                "approved": approved,
                "rejected": rejected,
                "pending": await self._count_messages(db, MessageStatus.pending),
            },
        }

    @staticmethod
    async def _count_messages(db: AsyncSession, status: MessageStatus) -> int:
        value = await db.scalar(
            select(func.count()).select_from(Message).where(Message.status == status),
        )
        return int(value or 0)

    @staticmethod
    async def _count_messages_since(
        db: AsyncSession,
        cutoff: datetime,
        *,
        statuses: tuple[MessageStatus, ...],
        timestamp_column=Message.prepared_at,
    ) -> int:
        value = await db.scalar(
            select(func.count())
            .select_from(Message)
            .where(
                Message.status.in_(statuses),
                timestamp_column.isnot(None),
                timestamp_column >= cutoff,
            ),
        )
        return int(value or 0)

    async def _top_procedures_for_messages_since(
        self,
        db: AsyncSession,
        cutoff: datetime,
        *,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        row_num = func.row_number().over(
            partition_by=Client.id,
            order_by=Record.record_datetime.desc(),
        ).label("rn")

        ranked_records = (
            select(
                Client.id.label("client_id"),
                Record.service_id.label("service_id"),
                row_num,
            )
            .select_from(Client)
            .join(Record, Record.client_id == Client.external_id)
            .where(
                Record.service_id.isnot(None),
                Record.record_datetime.isnot(None),
                Record.record_datetime < func.now(),
                Record.attendance.in_(rules.COMPLETED_ATTENDANCE_VALUES),
            )
            .subquery()
        )

        latest_records = (
            select(ranked_records.c.client_id, ranked_records.c.service_id)
            .where(ranked_records.c.rn == 1)
            .subquery()
        )

        stmt = (
            select(Procedure.name, func.count(Message.id))
            .select_from(Message)
            .join(latest_records, latest_records.c.client_id == Message.client_id)
            .join(Procedure, Procedure.external_id == latest_records.c.service_id)
            .where(Message.prepared_at >= cutoff)
            .group_by(Procedure.name)
            .order_by(func.count(Message.id).desc())
            .limit(limit)
        )

        rows = (await db.execute(stmt)).all()
        return [
            {"procedure_name": row[0], "count": int(row[1])}
            for row in rows
            if row[0]
        ]
