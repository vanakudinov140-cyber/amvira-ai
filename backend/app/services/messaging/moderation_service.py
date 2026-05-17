"""Модерация retention-сообщений (approve / reject / edit / regenerate / reset)."""

from __future__ import annotations

import logging
from typing import Literal, cast

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MessageStatus, MessageVersionSource
from app.models.message import Message
from app.models.message_version import MessageVersion
from app.services.ai.rewrite_service import RewriteService
from app.services.explainability.service import ExplainabilityService
from app.services.feedback.service import FeedbackService
from app.services.messaging.service import MessagingService
from app.services.retention.rules import RetentionAction
from app.services.retention.schemas import RetentionCandidate
from app.services.retention.service import RetentionService

logger = logging.getLogger(__name__)


class ModerationService:
    def __init__(
        self,
        retention: RetentionService | None = None,
        messaging: MessagingService | None = None,
        rewrite: RewriteService | None = None,
        explainability: ExplainabilityService | None = None,
        feedback: FeedbackService | None = None,
    ) -> None:
        self._retention = retention or RetentionService()
        self._messaging = messaging or MessagingService()
        self._rewrite = rewrite or RewriteService()
        self._explainability = explainability or ExplainabilityService()
        self._feedback = feedback or FeedbackService()

    async def get_message(self, db: AsyncSession, message_id: int) -> Message:
        message = await db.get(Message, message_id)
        if message is None:
            raise HTTPException(status_code=404, detail="Сообщение не найдено")
        return message

    async def _record_version(
        self,
        db: AsyncSession,
        *,
        message_id: int,
        old_content: str,
        new_content: str,
        source: MessageVersionSource,
    ) -> MessageVersion:
        version = MessageVersion(
            message_id=message_id,
            old_content=old_content,
            new_content=new_content,
            source=source,
        )
        db.add(version)
        await db.flush()
        return version

    async def list_versions(
        self,
        db: AsyncSession,
        message_id: int,
        *,
        limit: int = 20,
    ) -> list[MessageVersion]:
        await self.get_message(db, message_id)
        stmt = (
            select(MessageVersion)
            .where(MessageVersion.message_id == message_id)
            .order_by(MessageVersion.created_at.desc())
            .limit(limit)
        )
        return list((await db.execute(stmt)).scalars().all())

    async def approve(self, db: AsyncSession, message_id: int) -> Message:
        message = await self.get_message(db, message_id)
        if message.status != MessageStatus.pending:
            raise HTTPException(
                status_code=400,
                detail=f"approve доступен только для pending, текущий статус: {message.status.value}",
            )
        message.status = MessageStatus.approved
        await self._feedback.record_approve(db, message.id)
        logger.info(
            "message approved: message_id=%s client_id=%s action=%s",
            message.id,
            message.client_id,
            message.action,
        )
        return message

    async def reject(self, db: AsyncSession, message_id: int) -> Message:
        message = await self.get_message(db, message_id)
        if message.status != MessageStatus.pending:
            raise HTTPException(
                status_code=400,
                detail=f"reject доступен только для pending, текущий статус: {message.status.value}",
            )
        message.status = MessageStatus.rejected
        await self._feedback.record_reject(db, message.id)
        logger.info(
            "message rejected: message_id=%s client_id=%s action=%s",
            message.id,
            message.client_id,
            message.action,
        )
        return message

    async def reset(self, db: AsyncSession, message_id: int) -> Message:
        message = await self.get_message(db, message_id)
        if message.status not in (
            MessageStatus.rejected,
            MessageStatus.failed,
            MessageStatus.sent,
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "reset доступен только для rejected/failed/sent, "
                    f"текущий статус: {message.status.value}"
                ),
            )
        message.status = MessageStatus.pending
        message.sent_at = None
        logger.info(
            "message reset to pending: message_id=%s client_id=%s previous_flow=moderation",
            message.id,
            message.client_id,
        )
        return message

    async def update_text(self, db: AsyncSession, message_id: int, text: str) -> Message:
        message = await self.get_message(db, message_id)
        if message.status not in (MessageStatus.pending, MessageStatus.approved):
            raise HTTPException(
                status_code=400,
                detail=(
                    "редактирование доступно только для pending/approved, "
                    f"текущий статус: {message.status.value}"
                ),
            )
        stripped = text.strip()
        if not stripped:
            raise HTTPException(status_code=400, detail="text не может быть пустым")

        old_text = message.text
        if old_text != stripped:
            await self._record_version(
                db,
                message_id=message.id,
                old_content=old_text,
                new_content=stripped,
                source=MessageVersionSource.manual,
            )
            message.text = stripped
            await self._feedback.record_edit(db, message, old_text=old_text, new_text=stripped)

        logger.info(
            "message edited: message_id=%s client_id=%s action=%s text_length=%s",
            message.id,
            message.client_id,
            message.action,
            len(stripped),
        )
        return message

    async def regenerate(self, db: AsyncSession, message_id: int) -> Message:
        message = await self.get_message(db, message_id)
        if message.status not in (MessageStatus.pending, MessageStatus.approved):
            raise HTTPException(
                status_code=400,
                detail=(
                    "regenerate доступен только для pending/approved, "
                    f"текущий статус: {message.status.value}"
                ),
            )

        context = await self._retention.get_client_retention_context(db, message.client_id)
        if context is None:
            raise HTTPException(
                status_code=400,
                detail="Нет данных завершённого визита для перегенерации текста",
            )

        action = cast(RetentionAction, message.action)
        channel = cast(Literal["telegram", "sms"], message.channel)
        candidate = context.model_copy(
            update={
                "recommended_action": action,
                "recommended_channel": channel,
            },
        )

        template = self._messaging.generate_message(candidate)
        new_text = await self._rewrite.rewrite_retention_message(
            original_text=template.text,
            client_name=candidate.client_name,
            procedure_name=candidate.procedure_name,
            action=action,
            days_since_visit=candidate.days_since_visit,
            client_id=candidate.client_id,
        )

        old_text = message.text
        if old_text != new_text:
            await self._record_version(
                db,
                message_id=message.id,
                old_content=old_text,
                new_content=new_text,
                source=MessageVersionSource.regenerate,
            )
            message.text = new_text

        message.message_metadata = await self._explainability.build_metadata_for_client(
            db,
            client_id=message.client_id,
            action=message.action,
            days_since_visit=candidate.days_since_visit,
        )
        await self._feedback.record_regenerate(db, message)

        logger.info(
            "message regenerated: message_id=%s client_id=%s action=%s text_length=%s",
            message.id,
            message.client_id,
            message.action,
            len(new_text),
        )
        return message

    async def list_queue(
        self,
        db: AsyncSession,
        *,
        status: MessageStatus | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Message], int]:
        filters = []
        if status is not None:
            filters.append(Message.status == status)

        count_stmt = select(func.count()).select_from(Message)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = int(await db.scalar(count_stmt) or 0)

        stmt = select(Message).order_by(Message.prepared_at.desc()).limit(limit).offset(offset)
        if filters:
            stmt = stmt.where(*filters)

        rows = (await db.execute(stmt)).scalars().all()
        return list(rows), total
