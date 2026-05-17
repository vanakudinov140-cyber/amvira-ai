from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.message_serializers import build_message_payload
from app.api.deps import (
    SessionDep,
    get_flowsell_service,
    get_message_preparation_service,
    get_moderation_service,
)
from app.integrations.flowsell.service import FlowsellService
from app.models.enums import MessageStatus, MessageVersionSource
from app.models.message import Message
from app.services.message_preparation.service import MessagePreparationService
from app.services.messaging.moderation_service import ModerationService

router = APIRouter(prefix="/messages", tags=["messages"])


class PrepareRetentionResponse(BaseModel):
    success: bool = True
    prepared: int = Field(ge=0)


class MessageItem(BaseModel):
    id: int
    client_id: int
    text: str
    channel: str
    action: str
    status: MessageStatus
    prepared_at: datetime
    sent_at: datetime | None
    metadata: dict[str, Any] | None = None
    explain: list[str] = Field(default_factory=list)


async def _to_message_item(db: SessionDep, message: Message) -> MessageItem:
    payload = await build_message_payload(db, message)
    return MessageItem(**payload)


class PendingMessagesResponse(BaseModel):
    items: list[MessageItem]


class ModerationQueueResponse(BaseModel):
    items: list[MessageItem]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class MessageActionResponse(BaseModel):
    success: bool = True
    message: MessageItem


class UpdateMessageRequest(BaseModel):
    text: str = Field(min_length=1)


class MessageVersionItem(BaseModel):
    id: int
    message_id: int
    old_content: str
    new_content: str
    source: MessageVersionSource
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageVersionsResponse(BaseModel):
    items: list[MessageVersionItem]


class SendPendingResponse(BaseModel):
    success: bool = True
    sent: int = Field(ge=0)
    failed: int = Field(ge=0)


class StatsResponse(BaseModel):
    pending: int = Field(ge=0)
    approved: int = Field(ge=0)
    rejected: int = Field(ge=0)
    sent: int = Field(ge=0)
    failed: int = Field(ge=0)


@router.post("/prepare-retention", response_model=PrepareRetentionResponse)
async def prepare_retention_messages(
    db: SessionDep,
    service: Annotated[MessagePreparationService, Depends(get_message_preparation_service)],
) -> PrepareRetentionResponse:
    try:
        n = await service.prepare_retention_messages(db)
        await db.commit()
        return PrepareRetentionResponse(prepared=n)
    except Exception:
        await db.rollback()
        raise


@router.get("/pending", response_model=PendingMessagesResponse)
async def list_pending_messages(db: SessionDep) -> PendingMessagesResponse:
    stmt = (
        select(Message)
        .where(Message.status == MessageStatus.pending)
        .order_by(Message.prepared_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    items = [await _to_message_item(db, m) for m in rows]
    return PendingMessagesResponse(items=items)


@router.get("/moderation-queue", response_model=ModerationQueueResponse)
async def moderation_queue(
    db: SessionDep,
    moderation: Annotated[ModerationService, Depends(get_moderation_service)],
    status: MessageStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ModerationQueueResponse:
    items, total = await moderation.list_queue(db, status=status, limit=limit, offset=offset)
    serialized = [await _to_message_item(db, m) for m in items]
    return ModerationQueueResponse(
        items=serialized,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/send-pending", response_model=SendPendingResponse)
async def send_pending_messages(
    db: SessionDep,
    service: Annotated[FlowsellService, Depends(get_flowsell_service)],
) -> SendPendingResponse:
    try:
        sent, failed = await service.send_pending_messages(db)
        await db.commit()
        return SendPendingResponse(sent=sent, failed=failed)
    except Exception:
        await db.rollback()
        raise


@router.get("/stats", response_model=StatsResponse)
async def message_stats(db: SessionDep) -> StatsResponse:
    data = await FlowsellService.get_message_stats(db)
    return StatsResponse(**data)


@router.get("/{message_id}/versions", response_model=MessageVersionsResponse)
async def list_message_versions(
    message_id: int,
    db: SessionDep,
    moderation: Annotated[ModerationService, Depends(get_moderation_service)],
    limit: int = Query(default=20, ge=1, le=100),
) -> MessageVersionsResponse:
    versions = await moderation.list_versions(db, message_id, limit=limit)
    return MessageVersionsResponse(
        items=[MessageVersionItem.model_validate(v) for v in versions],
    )


@router.patch("/{message_id}", response_model=MessageActionResponse)
async def update_message(
    message_id: int,
    body: UpdateMessageRequest,
    db: SessionDep,
    moderation: Annotated[ModerationService, Depends(get_moderation_service)],
) -> MessageActionResponse:
    try:
        message = await moderation.update_text(db, message_id, body.text)
        await db.commit()
        return MessageActionResponse(message=await _to_message_item(db, message))
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise


@router.post("/{message_id}/regenerate", response_model=MessageActionResponse)
async def regenerate_message(
    message_id: int,
    db: SessionDep,
    moderation: Annotated[ModerationService, Depends(get_moderation_service)],
) -> MessageActionResponse:
    try:
        message = await moderation.regenerate(db, message_id)
        await db.commit()
        return MessageActionResponse(message=await _to_message_item(db, message))
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise


@router.post("/{message_id}/approve", response_model=MessageActionResponse)
async def approve_message(
    message_id: int,
    db: SessionDep,
    moderation: Annotated[ModerationService, Depends(get_moderation_service)],
) -> MessageActionResponse:
    try:
        message = await moderation.approve(db, message_id)
        await db.commit()
        return MessageActionResponse(message=await _to_message_item(db, message))
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise


@router.post("/{message_id}/reject", response_model=MessageActionResponse)
async def reject_message(
    message_id: int,
    db: SessionDep,
    moderation: Annotated[ModerationService, Depends(get_moderation_service)],
) -> MessageActionResponse:
    try:
        message = await moderation.reject(db, message_id)
        await db.commit()
        return MessageActionResponse(message=await _to_message_item(db, message))
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise


@router.post("/{message_id}/reset", response_model=MessageActionResponse)
async def reset_message(
    message_id: int,
    db: SessionDep,
    moderation: Annotated[ModerationService, Depends(get_moderation_service)],
) -> MessageActionResponse:
    try:
        message = await moderation.reset(db, message_id)
        await db.commit()
        return MessageActionResponse(message=await _to_message_item(db, message))
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise
