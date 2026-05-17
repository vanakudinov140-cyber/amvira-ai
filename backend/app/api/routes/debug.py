"""Временные debug-эндпоинты для диагностики."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.models.client import Client
from app.models.procedure import Procedure
from app.models.record import Record
from app.core.config import get_settings
from app.services.ai.rewrite_service import RewriteService
from app.services.messaging.safeguards import count_daily_sent, is_quiet_hours_active
from app.services.retention import rules
from app.services.retention.rules import RetentionAction

router = APIRouter(prefix="/debug", tags=["debug"])


class RecordSampleItem(BaseModel):
    id: int
    client_id: int | None
    datetime: datetime | None
    attendance: int | None
    save_sum: Decimal | None
    service_id: int | None


class RecordsSampleResponse(BaseModel):
    items: list[RecordSampleItem]


@router.get("/records-sample", response_model=RecordsSampleResponse)
async def records_sample(db: SessionDep) -> RecordsSampleResponse:
    """Первые 10 записей из таблицы records (временно, для retention)."""
    result = await db.execute(select(Record).order_by(Record.id).limit(10))
    items = [
        RecordSampleItem(
            id=row.id,
            client_id=row.client_id,
            datetime=row.record_datetime,
            attendance=row.attendance,
            save_sum=row.save_sum,
            service_id=row.service_id,
        )
        for row in result.scalars().all()
    ]
    return RecordsSampleResponse(items=items)


class AttendanceValueCount(BaseModel):
    attendance: int | None
    count: int


class AttendanceStatsResponse(BaseModel):
    attendance_values: list[AttendanceValueCount]


@router.get("/attendance-stats", response_model=AttendanceStatsResponse)
async def attendance_stats(db: SessionDep) -> AttendanceStatsResponse:
    """Распределение attendance в таблице records (временно, для диагностики)."""
    result = await db.execute(
        select(Record.attendance, func.count())
        .group_by(Record.attendance)
        .order_by(Record.attendance.nullsfirst()),
    )
    values = [
        AttendanceValueCount(attendance=row[0], count=row[1])
        for row in result.all()
    ]
    return AttendanceStatsResponse(attendance_values=values)


class UnmatchedClientSample(BaseModel):
    record_client_id: int | None
    matched_client_external_id: int | None


class UnmatchedProcedureSample(BaseModel):
    record_service_id: int | None
    matched_procedure_external_id: int | None


class RetentionPipelineResponse(BaseModel):
    total_records: int
    past_records: int
    completed_records: int
    latest_records_per_client: int
    joined_clients: int
    joined_procedures: int
    final_candidates: int
    sample_unmatched_clients: list[UnmatchedClientSample]
    sample_unmatched_procedures: list[UnmatchedProcedureSample]


_SAMPLE_LIMIT = 10


@router.get("/retention-pipeline", response_model=RetentionPipelineResponse)
async def retention_pipeline(db: SessionDep) -> RetentionPipelineResponse:
    """Этапы retention pipeline (временно, для диагностики потерь записей)."""
    total_records = await db.scalar(select(func.count()).select_from(Record)) or 0

    past_records = await db.scalar(
        select(func.count())
        .select_from(Record)
        .where(
            Record.record_datetime.isnot(None),
            Record.record_datetime < func.now(),
        ),
    ) or 0

    completed_records = await db.scalar(
        select(func.count())
        .select_from(Record)
        .where(
            Record.record_datetime.isnot(None),
            Record.record_datetime < func.now(),
            Record.attendance.in_(rules.COMPLETED_ATTENDANCE_VALUES),
            Record.client_id.isnot(None),
            Record.service_id.isnot(None),
        ),
    ) or 0

    joined_clients = await db.scalar(
        select(func.count())
        .select_from(Record)
        .join(Client, Client.external_id == Record.client_id)
        .where(
            Record.record_datetime.isnot(None),
            Record.record_datetime < func.now(),
            Record.attendance.in_(rules.COMPLETED_ATTENDANCE_VALUES),
            Record.client_id.isnot(None),
            Record.service_id.isnot(None),
        ),
    ) or 0

    joined_procedures = await db.scalar(
        select(func.count())
        .select_from(Record)
        .join(Client, Client.external_id == Record.client_id)
        .join(Procedure, Procedure.external_id == Record.service_id)
        .where(
            Record.record_datetime.isnot(None),
            Record.record_datetime < func.now(),
            Record.attendance.in_(rules.COMPLETED_ATTENDANCE_VALUES),
            Record.client_id.isnot(None),
            Record.service_id.isnot(None),
        ),
    ) or 0

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

    latest_records_per_client = await db.scalar(
        select(func.count()).select_from(ranked).where(ranked.c.rn == 1),
    ) or 0

    latest_rows = await db.execute(
        select(Record, Procedure)
        .where(Record.id.in_(select(ranked.c.record_id).where(ranked.c.rn == 1)))
        .join(Client, Client.external_id == Record.client_id)
        .join(Procedure, Procedure.external_id == Record.service_id),
    )

    today = date.today()
    final_candidates = 0
    for record, procedure in latest_rows.all():
        if record.record_datetime is None:
            continue
        days_since = (today - record.record_datetime.date()).days
        if days_since < 0:
            days_since = 0
        if rules.is_retention_eligible(days_since, procedure.reminder_min_days):
            final_candidates += 1

    unmatched_clients_result = await db.execute(
        select(Record.client_id, Client.external_id)
        .select_from(Record)
        .outerjoin(Client, Client.external_id == Record.client_id)
        .where(
            Record.record_datetime.isnot(None),
            Record.record_datetime < func.now(),
            Record.attendance.in_(rules.COMPLETED_ATTENDANCE_VALUES),
            Record.client_id.isnot(None),
            Client.id.is_(None),
        )
        .limit(_SAMPLE_LIMIT),
    )
    sample_unmatched_clients = [
        UnmatchedClientSample(
            record_client_id=row[0],
            matched_client_external_id=row[1],
        )
        for row in unmatched_clients_result.all()
    ]

    unmatched_procedures_result = await db.execute(
        select(Record.service_id, Procedure.external_id)
        .select_from(Record)
        .join(Client, Client.external_id == Record.client_id)
        .outerjoin(Procedure, Procedure.external_id == Record.service_id)
        .where(
            Record.record_datetime.isnot(None),
            Record.record_datetime < func.now(),
            Record.attendance.in_(rules.COMPLETED_ATTENDANCE_VALUES),
            Record.client_id.isnot(None),
            Record.service_id.isnot(None),
            Procedure.id.is_(None),
        )
        .limit(_SAMPLE_LIMIT),
    )
    sample_unmatched_procedures = [
        UnmatchedProcedureSample(
            record_service_id=row[0],
            matched_procedure_external_id=row[1],
        )
        for row in unmatched_procedures_result.all()
    ]

    return RetentionPipelineResponse(
        total_records=total_records,
        past_records=past_records,
        completed_records=completed_records,
        latest_records_per_client=latest_records_per_client,
        joined_clients=joined_clients,
        joined_procedures=joined_procedures,
        final_candidates=final_candidates,
        sample_unmatched_clients=sample_unmatched_clients,
        sample_unmatched_procedures=sample_unmatched_procedures,
    )


class MessagingSafeguardsResponse(BaseModel):
    daily_sent: int
    daily_limit: int
    quiet_hours_active: bool
    cooldown_days: int
    duplicate_window_days: int


@router.get("/messaging-safeguards", response_model=MessagingSafeguardsResponse)
async def messaging_safeguards(db: SessionDep) -> MessagingSafeguardsResponse:
    """Текущее состояние safeguards для retention messaging."""
    settings = get_settings()
    daily_sent = await count_daily_sent(db, settings)
    return MessagingSafeguardsResponse(
        daily_sent=daily_sent,
        daily_limit=settings.DAILY_SEND_LIMIT,
        quiet_hours_active=is_quiet_hours_active(settings=settings),
        cooldown_days=settings.RETENTION_COOLDOWN_DAYS,
        duplicate_window_days=settings.DUPLICATE_WINDOW_DAYS,
    )


class RewritePreviewRequest(BaseModel):
    text: str
    client_name: str = "Клиент"
    procedure_name: str = "Процедура"
    action: RetentionAction = "monthly_care"
    days_since_visit: int = 45


class RewritePreviewResponse(BaseModel):
    original: str
    rewritten: str


@router.post("/rewrite-preview", response_model=RewritePreviewResponse)
async def rewrite_preview(body: RewritePreviewRequest) -> RewritePreviewResponse:
    """Превью AI rewrite (mock) без сохранения в БД."""
    rewrite = RewriteService(get_settings())
    rewritten = await rewrite.rewrite_retention_message(
        original_text=body.text,
        client_name=body.client_name,
        procedure_name=body.procedure_name,
        action=body.action,
        days_since_visit=body.days_since_visit,
    )
    return RewritePreviewResponse(original=body.text, rewritten=rewritten)
