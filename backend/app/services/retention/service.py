"""Сервис retention: последний завершённый визит на клиента и отбор кандидатов."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.procedure import Procedure
from app.models.record import Record

from . import rules
from .schemas import RetentionCandidate

logger = logging.getLogger(__name__)


def _client_display_name(client: Client) -> str:
    parts = [client.first_name or "", client.last_name or ""]
    name = " ".join(p for p in parts if p).strip()
    return name if name else "Unknown"


class RetentionService:
    async def _log_records_diagnostics(self, db: AsyncSession) -> None:
        total = await db.scalar(select(func.count()).select_from(Record)) or 0

        future_count = await db.scalar(
            select(func.count())
            .select_from(Record)
            .where(
                Record.record_datetime.is_(None) | (Record.record_datetime >= func.now()),
            ),
        ) or 0

        attendance_rows = await db.execute(
            select(Record.attendance, func.count())
            .group_by(Record.attendance)
            .order_by(Record.attendance.nullsfirst()),
        )
        attendance_distribution = {
            row[0]: row[1] for row in attendance_rows.all()
        }

        logger.info(
            "retention records: total=%s future_or_null_datetime=%s attendance_distribution=%s",
            total,
            future_count,
            attendance_distribution,
        )

    async def get_retention_candidates(self, db: AsyncSession) -> list[RetentionCandidate]:
        await self._log_records_diagnostics(db)

        row_num = func.row_number().over(
            partition_by=Client.id,
            order_by=(Record.record_datetime.desc(), Record.id.desc()),
        ).label("rn")

        ranked = (
            select(Record.id.label("record_id"), row_num)
            .select_from(Record)
            .join(Client, Client.external_id == Record.client_id)
            .join(Procedure, Procedure.external_id == Record.service_id)
            .where(
                Record.record_datetime.isnot(None),
                Record.record_datetime < func.now(),
                Record.attendance.in_(rules.COMPLETED_ATTENDANCE_VALUES),
                Record.client_id.isnot(None),
                Record.service_id.isnot(None),
            )
            .subquery()
        )

        latest_record_ids = select(ranked.c.record_id).where(ranked.c.rn == 1)

        stmt = (
            select(Record, Client, Procedure)
            .where(Record.id.in_(latest_record_ids))
            .join(Client, Client.external_id == Record.client_id)
            .join(Procedure, Procedure.external_id == Record.service_id)
        )

        result = await db.execute(stmt)
        rows = result.all()

        past_completed_count = await db.scalar(
            select(func.count())
            .select_from(Record)
            .where(
                Record.record_datetime.isnot(None),
                Record.record_datetime < func.now(),
                Record.attendance.in_(rules.COMPLETED_ATTENDANCE_VALUES),
            ),
        ) or 0

        logger.info(
            "retention records: past_completed=%s latest_per_client=%s",
            past_completed_count,
            len(rows),
        )

        today = date.today()
        candidates: list[RetentionCandidate] = []
        attendance_seen: Counter[int | None] = Counter()
        via_default_threshold = 0
        via_custom_reminder_min_days = 0

        for record, client, procedure in rows:
            attendance_seen[record.attendance] += 1
            if record.record_datetime is None:
                continue

            last_visit_date = record.record_datetime.date()
            days_since = (today - last_visit_date).days
            if days_since < 0:
                days_since = 0

            if not rules.is_retention_eligible(days_since, procedure.reminder_min_days):
                continue

            if procedure.reminder_min_days is None:
                via_default_threshold += 1
            else:
                via_custom_reminder_min_days += 1

            candidates.append(
                RetentionCandidate(
                    client_id=client.id,
                    client_name=_client_display_name(client),
                    procedure_name=procedure.name,
                    last_visit_date=last_visit_date,
                    days_since_visit=days_since,
                    recommended_action=rules.recommend_action(days_since),
                    recommended_channel=rules.recommend_channel(client.telegram),
                ),
            )

        logger.info(
            "retention: найдено %s кандидатов из %s клиентов "
            "(via_default_threshold=%s via_custom_reminder_min_days=%s attendance=%s)",
            len(candidates),
            len(rows),
            via_default_threshold,
            via_custom_reminder_min_days,
            dict(attendance_seen),
        )
        return candidates

    async def get_client_retention_context(
        self,
        db: AsyncSession,
        client_id: int,
    ) -> RetentionCandidate | None:
        """Контекст последнего завершённого визита клиента (read-only, для regenerate)."""
        stmt = (
            select(Record, Client, Procedure)
            .join(Client, Client.external_id == Record.client_id)
            .join(Procedure, Procedure.external_id == Record.service_id)
            .where(
                Client.id == client_id,
                Record.record_datetime.isnot(None),
                Record.record_datetime < func.now(),
                Record.attendance.in_(rules.COMPLETED_ATTENDANCE_VALUES),
                Record.client_id.isnot(None),
                Record.service_id.isnot(None),
            )
            .order_by(Record.record_datetime.desc(), Record.id.desc())
            .limit(1)
        )
        row = (await db.execute(stmt)).first()
        if row is None:
            return None

        record, client, procedure = row
        if record.record_datetime is None:
            return None

        today = date.today()
        last_visit_date = record.record_datetime.date()
        days_since = max(0, (today - last_visit_date).days)

        return RetentionCandidate(
            client_id=client.id,
            client_name=_client_display_name(client),
            procedure_name=procedure.name,
            last_visit_date=last_visit_date,
            days_since_visit=days_since,
            recommended_action=rules.recommend_action(days_since),
            recommended_channel=rules.recommend_channel(client.telegram),
        )
