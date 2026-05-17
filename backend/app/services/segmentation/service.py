"""MVP-сегментация клиентов по визитам, чеку и давности."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.record import Record
from app.services.retention import rules
from app.services.segmentation.schemas import ClientSegment

HIGH_CHECK_THRESHOLD = 5000.0
LOYAL_MIN_VISITS = 5
ACTIVE_MAX_DAYS_ABSENT = 45
SLEEPING_MIN_DAYS_ABSENT = 60
LOST_VIP_MIN_DAYS_ABSENT = 120


@dataclass(frozen=True)
class ClientVisitProfile:
    client_id: int
    visit_count: int
    days_since_last_visit: int
    previous_visit_frequency_days: int | None
    average_check: float
    segment: ClientSegment


class SegmentationService:
    async def get_client_visit_profile(
        self,
        db: AsyncSession,
        client_id: int,
        *,
        as_of: date | None = None,
    ) -> ClientVisitProfile | None:
        client = await db.get(Client, client_id)
        if client is None:
            return None

        stmt = (
            select(Record)
            .where(
                Record.client_id == client.external_id,
                Record.record_datetime.isnot(None),
                Record.record_datetime < func.now(),
                Record.attendance.in_(rules.COMPLETED_ATTENDANCE_VALUES),
            )
            .order_by(Record.record_datetime.asc())
        )
        records = list((await db.execute(stmt)).scalars().all())
        if not records:
            return None

        today = as_of or date.today()
        last_dt = records[-1].record_datetime
        assert last_dt is not None
        days_since = max(0, (today - last_dt.date()).days)

        visit_count = len(records)
        frequency = self._average_frequency_days(records)
        average_check = self._average_check(records)
        segment = classify_segment(
            visit_count=visit_count,
            days_since_last=days_since,
            average_check=average_check,
            average_frequency_days=frequency,
        )

        return ClientVisitProfile(
            client_id=client_id,
            visit_count=visit_count,
            days_since_last_visit=days_since,
            previous_visit_frequency_days=frequency,
            average_check=average_check,
            segment=segment,
        )

    @staticmethod
    def _average_check(records: list[Record]) -> float:
        amounts = [
            float(r.save_sum)
            for r in records
            if r.save_sum is not None and float(r.save_sum) > 0
        ]
        if not amounts:
            return 0.0
        return sum(amounts) / len(amounts)

    @staticmethod
    def _average_frequency_days(records: list[Record]) -> int | None:
        if len(records) < 2:
            return None
        gaps: list[int] = []
        prev = records[0].record_datetime
        for record in records[1:]:
            current = record.record_datetime
            if prev is None or current is None:
                continue
            gap = (current.date() - prev.date()).days
            if gap > 0:
                gaps.append(gap)
            prev = current
        if not gaps:
            return None
        return int(round(sum(gaps) / len(gaps)))


def classify_segment(
    *,
    visit_count: int,
    days_since_last: int,
    average_check: float,
    average_frequency_days: int | None,
) -> ClientSegment:
    if visit_count <= 1:
        return "new"

    if days_since_last >= LOST_VIP_MIN_DAYS_ABSENT and average_check >= HIGH_CHECK_THRESHOLD:
        return "lost_vip"

    if days_since_last >= SLEEPING_MIN_DAYS_ABSENT:
        return "sleeping"

    if (
        visit_count >= LOYAL_MIN_VISITS
        and average_frequency_days is not None
        and average_frequency_days <= 35
        and days_since_last < ACTIVE_MAX_DAYS_ABSENT
    ):
        return "loyal"

    if days_since_last < ACTIVE_MAX_DAYS_ABSENT:
        return "active"

    return "sleeping"


def is_high_average_check(average_check: float) -> bool:
    return average_check >= HIGH_CHECK_THRESHOLD
