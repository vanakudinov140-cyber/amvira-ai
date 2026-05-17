"""Отправка TEST retention-сообщений в Telegram Bot API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from app.core.config import Settings
from app.i18n.ru import label_action, label_segment

if TYPE_CHECKING:
    from app.models.message import Message

logger = logging.getLogger(__name__)

_TELEGRAM_TEXT_LIMIT = 4096
_TIMEOUT = httpx.Timeout(20.0, connect=8.0)


def _client_phone(message: Message) -> str:
    client = message.client
    phone = (client.phone or "").strip() if client else ""
    return phone or "(empty)"


def format_test_retention_message(message: Message) -> str:
    metadata = message.message_metadata or {}
    segment_raw = str(metadata.get("client_segment") or "unknown")
    segment = str(metadata.get("client_segment_label") or label_segment(segment_raw))
    action = str(metadata.get("recommended_action_label") or label_action(message.action))

    body = (
        "TEST RETENTION MESSAGE\n\n"
        f"Client ID: {message.client_id}\n"
        f"Segment: {segment}\n"
        f"Action: {action}\n"
        f"Original phone: {_client_phone(message)}\n\n"
        "Message:\n"
        f"{message.text}"
    )
    if len(body) > _TELEGRAM_TEXT_LIMIT:
        trimmed = body[: _TELEGRAM_TEXT_LIMIT - 20].rstrip()
        body = f"{trimmed}\n\n…(обрезано)"
    return body


class TelegramSender:
    def __init__(self, settings: Settings | None = None) -> None:
        from app.core.config import get_settings

        self._settings = settings or get_settings()
        self._token = (self._settings.TELEGRAM_BOT_TOKEN or "").strip()
        self._chat_id = (self._settings.TELEGRAM_TEST_CHAT_ID or "").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self._token and self._chat_id)

    async def send_test_retention_message(self, message: Message) -> bool:
        if not self.is_configured:
            return False

        text = format_test_retention_message(message)
        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        payload = {"chat_id": self._chat_id, "text": text, "disable_web_page_preview": True}

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        if not data.get("ok"):
            description = data.get("description", "unknown error")
            raise RuntimeError(f"Telegram API error: {description}")

        return True
