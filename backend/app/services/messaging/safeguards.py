"""Safeguards для retention messaging (duplicate, cooldown, daily limit, quiet hours)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.enums import MessageStatus
from app.models.message import Message

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def start_of_utc_day(moment: datetime | None = None) -> datetime:
    now = moment or utc_now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def is_quiet_hours_active(
    moment: datetime | None = None,
    *,
    settings: Settings | None = None,
) -> bool:
    """True, если текущее UTC-время в интервале quiet hours (включая переход через полночь)."""
    cfg = settings or get_settings()
    now = moment or utc_now()
    hour = now.hour
    start = cfg.QUIET_HOURS_START
    end = cfg.QUIET_HOURS_END

    if start == end:
        return False
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


async def count_daily_sent(db: AsyncSession, settings: Settings | None = None) -> int:
    cfg = settings or get_settings()
    day_start = start_of_utc_day()
    value = await db.scalar(
        select(func.count())
        .select_from(Message)
        .where(
            Message.status == MessageStatus.sent,
            Message.sent_at.isnot(None),
            Message.sent_at >= day_start,
        ),
    )
    return int(value or 0)


async def remaining_daily_send_quota(db: AsyncSession, settings: Settings | None = None) -> int:
    cfg = settings or get_settings()
    sent_today = await count_daily_sent(db, cfg)
    return max(0, cfg.DAILY_SEND_LIMIT - sent_today)


async def should_skip_retention_prepare(
    db: AsyncSession,
    client_id: int,
    settings: Settings | None = None,
) -> bool:
    """True — новое retention-сообщение создавать не нужно."""
    cfg = settings or get_settings()
    now = utc_now()
    duplicate_cutoff = now - timedelta(days=cfg.DUPLICATE_WINDOW_DAYS)
    cooldown_cutoff = now - timedelta(days=cfg.RETENTION_COOLDOWN_DAYS)

    duplicate_stmt = (
        select(Message.id)
        .where(
            Message.client_id == client_id,
            or_(
                and_(
                    Message.status == MessageStatus.pending,
                    Message.prepared_at >= duplicate_cutoff,
                ),
                and_(
                    Message.status == MessageStatus.approved,
                    Message.prepared_at >= duplicate_cutoff,
                ),
                and_(
                    Message.status == MessageStatus.sent,
                    or_(
                        Message.sent_at >= duplicate_cutoff,
                        Message.prepared_at >= duplicate_cutoff,
                    ),
                ),
            ),
        )
        .limit(1)
    )
    if (await db.execute(duplicate_stmt)).scalar_one_or_none() is not None:
        logger.info(
            "skip duplicate retention message client_id=%s "
            "(pending/sent within duplicate_window_days=%s)",
            client_id,
            cfg.DUPLICATE_WINDOW_DAYS,
        )
        return True

    cooldown_stmt = (
        select(Message.id)
        .where(
            Message.client_id == client_id,
            Message.status == MessageStatus.sent,
            Message.sent_at.isnot(None),
            Message.sent_at >= cooldown_cutoff,
        )
        .limit(1)
    )
    if (await db.execute(cooldown_stmt)).scalar_one_or_none() is not None:
        logger.info(
            "skip retention message client_id=%s (cooldown: sent within cooldown_days=%s)",
            client_id,
            cfg.RETENTION_COOLDOWN_DAYS,
        )
        return True

    return False
