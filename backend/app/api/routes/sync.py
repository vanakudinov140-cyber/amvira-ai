import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import SessionDep, get_yclients_sync_service
from app.integrations.yclients.exceptions import YclientsError
from app.integrations.yclients.service import YclientsSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["sync"])


class SyncResponse(BaseModel):
    success: bool = True
    synced: int


@router.post("/clients", response_model=SyncResponse)
async def sync_clients_route(
    db: SessionDep,
    service: Annotated[YclientsSyncService, Depends(get_yclients_sync_service)],
) -> SyncResponse:
    try:
        n = await service.sync_clients(db)
        await db.commit()
        return SyncResponse(synced=n)
    except YclientsError as exc:
        await db.rollback()
        logger.warning("sync_clients failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/procedures", response_model=SyncResponse)
async def sync_procedures_route(
    db: SessionDep,
    service: Annotated[YclientsSyncService, Depends(get_yclients_sync_service)],
) -> SyncResponse:
    try:
        n = await service.sync_procedures(db)
        await db.commit()
        return SyncResponse(synced=n)
    except YclientsError as exc:
        await db.rollback()
        logger.warning("sync_procedures failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/visits", response_model=SyncResponse)
async def sync_visits_route(
    db: SessionDep,
    service: Annotated[YclientsSyncService, Depends(get_yclients_sync_service)],
) -> SyncResponse:
    try:
        n = await service.sync_visits(db)
        await db.commit()
        return SyncResponse(synced=n)
    except YclientsError as exc:
        await db.rollback()
        logger.warning("sync_visits failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/records", response_model=SyncResponse)
async def sync_records_route(
    db: SessionDep,
    service: Annotated[YclientsSyncService, Depends(get_yclients_sync_service)],
) -> SyncResponse:
    try:
        n = await service.sync_records(db)
        await db.commit()
        return SyncResponse(synced=n)
    except YclientsError as exc:
        await db.rollback()
        logger.warning("sync_records failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
