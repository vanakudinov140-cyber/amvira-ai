"""Синхронизация сущностей YCLIENTS в локальную БД."""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.yclients.client import YclientsClient
from app.models.client import Client
from app.models.procedure import Procedure
from app.models.record import Record
from app.models.visit import Visit

logger = logging.getLogger(__name__)

_RECORDS_UPSERT_BATCH = 500


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return None


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value if value.strip() else None
    return str(value)


def _record_client_external_id(record: dict[str, Any]) -> int | None:
    cid = _as_int(record.get("client_id"))
    if cid is not None:
        return cid
    client = record.get("client")
    if isinstance(client, dict):
        return _as_int(client.get("id"))
    return None


def _first_service_external_id(record: dict[str, Any]) -> int | None:
    services = record.get("services")
    if not isinstance(services, list) or not services:
        return None
    first = services[0]
    if isinstance(first, dict):
        return _as_int(first.get("id"))
    return None


def _record_staff_external_id(record: dict[str, Any]) -> int | None:
    staff_id = _as_int(record.get("staff_id"))
    if staff_id is not None:
        return staff_id
    staff = record.get("staff")
    if isinstance(staff, dict):
        return _as_int(staff.get("id"))
    return None


def _parse_record_datetime(record: dict[str, Any]) -> datetime | None:
    raw = record.get("datetime") or record.get("date")
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    if "T" in raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            logger.debug("не удалось распарсить datetime=%s", raw)
    if " " in raw and len(raw) >= 19:
        try:
            return datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return None


def _record_save_sum(record: dict[str, Any]) -> Decimal | None:
    return _record_price(record)


def _parse_visit_date(record: dict[str, Any]) -> date | None:
    raw = record.get("datetime") or record.get("date")
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    if "T" in raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        except ValueError:
            logger.debug("не удалось распарсить datetime=%s", raw)
    if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            pass
    if " " in raw and len(raw) >= 19:
        try:
            return datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S").date()
        except ValueError:
            pass
    return None


def _record_price(record: dict[str, Any]) -> Decimal | None:
    services = record.get("services")
    if not isinstance(services, list) or not services:
        return None
    total = Decimal("0")
    any_cost = False
    for svc in services:
        if not isinstance(svc, dict):
            continue
        cost = svc.get("cost")
        if cost is None:
            continue
        try:
            total += Decimal(str(cost))
            any_cost = True
        except (InvalidOperation, ValueError, TypeError):
            logger.debug("пропуск стоимости услуги record=%s", record.get("id"))
    return total if any_cost else None


class YclientsSyncService:
    def __init__(self, yclients: YclientsClient) -> None:
        self._yclients = yclients

    async def sync_clients(self, db: AsyncSession) -> int:
        payload = await self._yclients.get_clients()
        external_ids: set[int] = set()
        for row in payload:
            ext = _as_int(row.get("id"))
            if ext is not None:
                external_ids.add(ext)

        if not external_ids:
            return 0

        result = await db.execute(select(Client).where(Client.external_id.in_(external_ids)))
        by_external: dict[int, Client] = {c.external_id: c for c in result.scalars().all()}

        synced = 0
        for raw in payload:
            ext = _as_int(raw.get("id"))
            if ext is None:
                continue

            entity = by_external.get(ext)
            if entity is None:
                entity = Client(external_id=ext)
                db.add(entity)
                by_external[ext] = entity

            entity.first_name = _as_str(raw.get("name"))
            entity.last_name = _as_str(raw.get("surname"))
            entity.phone = _as_str(raw.get("phone"))
            entity.telegram = _as_str(
                raw.get("telegram")
                or raw.get("tg_username")
                or raw.get("telegram_username"),
            )
            synced += 1

        await db.flush()
        logger.info("sync_clients: upsert %s строк", synced)
        return synced

    async def sync_procedures(self, db: AsyncSession) -> int:
        payload = await self._yclients.get_services()
        external_ids: set[int] = set()
        for row in payload:
            ext = _as_int(row.get("id"))
            if ext is not None:
                external_ids.add(ext)

        if not external_ids:
            return 0

        result = await db.execute(select(Procedure).where(Procedure.external_id.in_(external_ids)))
        by_external: dict[int, Procedure] = {p.external_id: p for p in result.scalars().all()}

        synced = 0
        for raw in payload:
            ext = _as_int(raw.get("id"))
            if ext is None:
                continue

            title = raw.get("title")
            if not isinstance(title, str) or not title.strip():
                continue

            entity = by_external.get(ext)
            if entity is None:
                entity = Procedure(external_id=ext, name=title.strip())
                db.add(entity)
                by_external[ext] = entity
            else:
                entity.name = title.strip()

            cat = raw.get("_category_title")
            entity.category = cat if isinstance(cat, str) and cat.strip() else None
            entity.reminder_min_days = None
            entity.reminder_max_days = None
            synced += 1

        await db.flush()
        logger.info("sync_procedures: upsert %s строк", synced)
        return synced

    async def sync_visits(self, db: AsyncSession) -> int:
        records = await self._yclients.get_records()

        client_ext_ids: set[int] = set()
        procedure_ext_ids: set[int] = set()
        record_ids: set[int] = set()

        for rec in records:
            if not isinstance(rec, dict):
                continue
            rid = _as_int(rec.get("id"))
            if rid is not None:
                record_ids.add(rid)
            ce = _record_client_external_id(rec)
            if ce is not None:
                client_ext_ids.add(ce)
            se = _first_service_external_id(rec)
            if se is not None:
                procedure_ext_ids.add(se)

        clients_map: dict[int, Client] = {}
        if client_ext_ids:
            cr = await db.execute(select(Client).where(Client.external_id.in_(client_ext_ids)))
            clients_map = {c.external_id: c for c in cr.scalars().all()}

        procedures_map: dict[int, Procedure] = {}
        if procedure_ext_ids:
            pr = await db.execute(
                select(Procedure).where(Procedure.external_id.in_(procedure_ext_ids)),
            )
            procedures_map = {p.external_id: p for p in pr.scalars().all()}

        visits_by_external: dict[int, Visit] = {}
        if record_ids:
            vr = await db.execute(select(Visit).where(Visit.external_id.in_(record_ids)))
            visits_by_external = {v.external_id: v for v in vr.scalars().all() if v.external_id}

        synced = 0
        for rec in records:
            if not isinstance(rec, dict):
                continue
            rid = _as_int(rec.get("id"))
            if rid is None:
                continue

            cli_ext = _record_client_external_id(rec)
            proc_ext = _first_service_external_id(rec)
            if cli_ext is None or proc_ext is None:
                logger.debug("sync_visits: пропуск записи id=%s (нет клиента или услуги)", rid)
                continue

            client = clients_map.get(cli_ext)
            procedure = procedures_map.get(proc_ext)
            if client is None or procedure is None:
                logger.warning(
                    "sync_visits: пропуск записи id=%s client_ext=%s proc_ext=%s (нет в БД)",
                    rid,
                    cli_ext,
                    proc_ext,
                )
                continue

            visit_date = _parse_visit_date(rec)
            if visit_date is None:
                logger.warning("sync_visits: пропуск записи id=%s (нет даты визита)", rid)
                continue

            visit = visits_by_external.get(rid)
            if visit is None:
                visit = Visit(
                    external_id=rid,
                    client_id=client.id,
                    procedure_id=procedure.id,
                    visit_date=visit_date,
                )
                db.add(visit)
                visits_by_external[rid] = visit
            else:
                visit.client_id = client.id
                visit.procedure_id = procedure.id
                visit.visit_date = visit_date

            staff = rec.get("staff")
            visit.master_name = (
                _as_str(staff.get("name")) if isinstance(staff, dict) else None
            )
            visit.comment = _as_str(rec.get("comment"))
            visit.price = _record_price(rec)
            synced += 1

        await db.flush()
        logger.info("sync_visits: upsert %s строк", synced)
        return synced

    async def sync_records(self, db: AsyncSession) -> int:
        payload = await self._yclients.get_records()
        rows: list[dict[str, Any]] = []

        for raw in payload:
            if not isinstance(raw, dict):
                continue
            yclients_id = _as_int(raw.get("id"))
            if yclients_id is None:
                continue

            attendance = _as_int(raw.get("attendance"))
            if attendance is None:
                attendance = _as_int(raw.get("visit_attendance"))

            rows.append(
                {
                    "yclients_record_id": yclients_id,
                    "client_id": _record_client_external_id(raw),
                    "staff_id": _record_staff_external_id(raw),
                    "service_id": _first_service_external_id(raw),
                    "datetime": _parse_record_datetime(raw),
                    "attendance": attendance,
                    "save_sum": _record_save_sum(raw),
                },
            )

        if not rows:
            logger.info("sync_records: получено 0 записей из YCLIENTS")
            return 0

        for offset in range(0, len(rows), _RECORDS_UPSERT_BATCH):
            batch = rows[offset : offset + _RECORDS_UPSERT_BATCH]
            stmt = pg_insert(Record).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Record.yclients_record_id],
                set_={
                    "client_id": stmt.excluded.client_id,
                    "staff_id": stmt.excluded.staff_id,
                    "service_id": stmt.excluded.service_id,
                    "datetime": stmt.excluded.datetime,
                    "attendance": stmt.excluded.attendance,
                    "save_sum": stmt.excluded.save_sum,
                },
            )
            await db.execute(stmt)

        logger.info("sync_records: upsert %s записей из YCLIENTS", len(rows))
        return len(rows)
