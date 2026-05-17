"""Сбор operator feedback по retention-сообщениям."""

from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.message_feedback import MessageFeedback
from app.services.feedback.utils import compute_edited_ratio, original_ai_text_from_metadata

logger = logging.getLogger(__name__)


class FeedbackService:
    async def ensure_feedback_row(self, db: AsyncSession, message_id: int) -> MessageFeedback:
        existing = await db.scalar(
            select(MessageFeedback).where(MessageFeedback.message_id == message_id),
        )
        if existing is not None:
            return existing

        row = MessageFeedback(message_id=message_id)
        db.add(row)
        await db.flush()
        return row

    async def init_for_message(self, db: AsyncSession, message: Message) -> MessageFeedback:
        feedback = await self.ensure_feedback_row(db, message.id)
        metadata = dict(message.message_metadata or {})
        if "original_ai_text" not in metadata:
            metadata["original_ai_text"] = message.text
            message.message_metadata = metadata
        return feedback

    async def record_approve(self, db: AsyncSession, message_id: int) -> None:
        feedback = await self.ensure_feedback_row(db, message_id)
        feedback.approved_by_operator = True
        logger.info("feedback: approve message_id=%s", message_id)

    async def record_reject(self, db: AsyncSession, message_id: int) -> None:
        feedback = await self.ensure_feedback_row(db, message_id)
        feedback.approved_by_operator = False
        logger.info("feedback: reject message_id=%s", message_id)

    async def record_edit(
        self,
        db: AsyncSession,
        message: Message,
        *,
        old_text: str,
        new_text: str,
    ) -> None:
        feedback = await self.ensure_feedback_row(db, message.id)
        baseline = original_ai_text_from_metadata(message.message_metadata) or old_text
        feedback.manually_edited = True
        feedback.edited_ratio = Decimal(str(compute_edited_ratio(baseline, new_text)))
        logger.info(
            "feedback: edit message_id=%s edited_ratio=%s",
            message.id,
            feedback.edited_ratio,
        )

    async def record_regenerate(self, db: AsyncSession, message: Message) -> None:
        metadata = dict(message.message_metadata or {})
        metadata["was_regenerated"] = True
        message.message_metadata = metadata
        await self.ensure_feedback_row(db, message.id)
