"""Подготовка сообщений retention: запись в БД без отправки."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.enums import MessageStatus
from app.models.message import Message
from app.services.ai.rewrite_service import RewriteService
from app.services.explainability.service import ExplainabilityService
from app.services.feedback.service import FeedbackService
from app.services.messaging.safeguards import should_skip_retention_prepare
from app.services.messaging.service import MessagingService
from app.services.retention.service import RetentionService

logger = logging.getLogger(__name__)


class MessagePreparationService:
    def __init__(
        self,
        retention: RetentionService,
        messaging: MessagingService,
        rewrite: RewriteService | None = None,
        explainability: ExplainabilityService | None = None,
        feedback: FeedbackService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._retention = retention
        self._messaging = messaging
        self._rewrite = rewrite or RewriteService()
        self._explainability = explainability or ExplainabilityService()
        self._feedback = feedback or FeedbackService()
        self._settings = settings or get_settings()

    async def prepare_retention_messages(self, db: AsyncSession) -> int:
        candidates = await self._retention.get_retention_candidates(db)
        prepared = 0
        skipped = 0

        for candidate in candidates:
            if await should_skip_retention_prepare(db, candidate.client_id, self._settings):
                skipped += 1
                continue

            template = self._messaging.generate_message(candidate)
            text = await self._rewrite.rewrite_retention_message(
                original_text=template.text,
                client_name=candidate.client_name,
                procedure_name=candidate.procedure_name,
                action=template.action,
                days_since_visit=candidate.days_since_visit,
                client_id=candidate.client_id,
            )

            metadata = await self._explainability.build_metadata_for_client(
                db,
                client_id=candidate.client_id,
                action=template.action,
                days_since_visit=candidate.days_since_visit,
            )

            message = Message(
                client_id=candidate.client_id,
                text=text,
                channel=template.channel,
                action=template.action,
                status=MessageStatus.pending,
                sent_at=None,
                message_metadata=metadata,
            )
            db.add(message)
            await db.flush()
            await self._feedback.init_for_message(db, message)
            prepared += 1

        await db.flush()
        logger.info(
            "message_preparation: подготовлено=%s пропущено_safeguards=%s кандидатов=%s "
            "ai_rewrite_enabled=%s",
            prepared,
            skipped,
            len(candidates),
            self._settings.AI_REWRITE_ENABLED,
        )
        return prepared
