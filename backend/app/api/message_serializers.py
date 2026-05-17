"""Сериализация Message → API item с explainability."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.services.explainability.service import ExplainabilityService


async def build_message_payload(
    db: AsyncSession,
    message: Message,
    explainability: ExplainabilityService | None = None,
) -> dict[str, object]:
    svc = explainability or ExplainabilityService()
    metadata = message.message_metadata
    if not metadata:
        metadata = await svc.build_metadata_for_client(
            db,
            client_id=message.client_id,
            action=message.action,
        )
    explain = svc.build_explain_lines(metadata)
    return {
        "id": message.id,
        "client_id": message.client_id,
        "text": message.text,
        "channel": message.channel,
        "action": message.action,
        "status": message.status,
        "prepared_at": message.prepared_at,
        "sent_at": message.sent_at,
        "metadata": metadata,
        "explain": explain,
    }
