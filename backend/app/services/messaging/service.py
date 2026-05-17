"""Генерация текста сообщения из шаблона (без AI и без отправки)."""

from __future__ import annotations

import logging

from app.services.messaging.schemas import MessageTemplate
from app.services.messaging.templates import TEMPLATES
from app.services.retention.rules import RetentionAction
from app.services.retention.schemas import RetentionCandidate

logger = logging.getLogger(__name__)


class MessagingService:
    def generate_message(self, candidate: RetentionCandidate) -> MessageTemplate:
        action: RetentionAction = candidate.recommended_action
        definition = TEMPLATES[action]

        context = {
            "client_name": candidate.client_name,
            "procedure_name": candidate.procedure_name,
            "days_since_visit": candidate.days_since_visit,
        }
        text = definition.text.format(**context)
        title = definition.title.format(**context)

        logger.info(
            "retention message selected: client_id=%s days_since_visit=%s action=%s template=%s",
            candidate.client_id,
            candidate.days_since_visit,
            action,
            action,
        )

        return MessageTemplate(
            title=title,
            text=text,
            action=action,
            channel=candidate.recommended_channel,
        )
