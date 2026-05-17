"""Отправка подготовленных сообщений через FlowSell (без ретраев и фона)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.integrations.flowsell.client import FlowsellClient, FlowsellSendResult
from app.integrations.telegram.sender import TelegramSender
from app.models.enums import MessageStatus
from app.models.message import Message
from app.services.messaging.safeguards import (
    count_daily_sent,
    is_quiet_hours_active,
    remaining_daily_send_quota,
)

logger = logging.getLogger(__name__)


class FlowsellService:
    def __init__(
        self,
        client: FlowsellClient | None,
        settings: Settings | None = None,
        telegram: TelegramSender | None = None,
    ) -> None:
        self._client = client
        self._settings = settings or get_settings()
        self._telegram = telegram if telegram is not None else TelegramSender(self._settings)

    @staticmethod
    async def get_message_stats(db: AsyncSession) -> dict[str, int]:
        pending = await FlowsellService._count_by_status(db, MessageStatus.pending)
        approved = await FlowsellService._count_by_status(db, MessageStatus.approved)
        rejected = await FlowsellService._count_by_status(db, MessageStatus.rejected)
        sent = await FlowsellService._count_by_status(db, MessageStatus.sent)
        failed = await FlowsellService._count_by_status(db, MessageStatus.failed)
        return {
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "sent": sent,
            "failed": failed,
        }

    @staticmethod
    async def _count_by_status(db: AsyncSession, status: MessageStatus) -> int:
        stmt = select(func.count()).select_from(Message).where(Message.status == status)
        value = await db.scalar(stmt)
        return int(value or 0)

    @staticmethod
    def _client_phone(message: Message) -> str | None:
        client = message.client
        phone = (client.phone or "").strip() if client else ""
        return phone or None

    def _resolve_phone(self, message: Message, recipient_index: int) -> str | None:
        if self._settings.TEST_MODE:
            recipients = self._settings.test_recipient_phones
            if not recipients:
                return None
            return recipients[recipient_index % len(recipients)]

        return self._client_phone(message)

    def _log_test_mode_redirect(self, message: Message, redirected_to: str) -> None:
        original_phone = self._client_phone(message) or "(empty)"
        logger.info(
            "TEST MODE ENABLED\n"
            "original_client_id=%s\n"
            "original_phone=%s\n"
            "redirected_to=%s",
            message.client_id,
            original_phone,
            redirected_to,
        )

    async def _send_test_message(self, message: Message, redirected_to: str) -> FlowsellSendResult:
        if self._telegram.is_configured:
            try:
                await self._telegram.send_test_retention_message(message)
                logger.info(
                    "TELEGRAM TEST SEND SUCCESS message_id=%s client_id=%s chat_id=%s",
                    message.id,
                    message.client_id,
                    self._settings.TELEGRAM_TEST_CHAT_ID,
                )
                return FlowsellSendResult(ok=True, detail="telegram")
            except Exception as exc:
                logger.warning(
                    "telegram test send failed, fallback to TEST SENDER: "
                    "message_id=%s client_id=%s error=%s",
                    message.id,
                    message.client_id,
                    exc,
                )

        logger.info(
            "TEST SEND: to=%s channel=%s text=%s",
            redirected_to,
            message.channel,
            message.text,
        )
        return FlowsellSendResult(ok=True, detail="test_sender")

    async def _send_message(
        self,
        *,
        phone: str,
        text: str,
        channel: str,
        message: Message | None = None,
    ) -> FlowsellSendResult:
        if self._settings.TEST_MODE:
            if message is None:
                raise RuntimeError("message обязателен для TEST_MODE send")
            return await self._send_test_message(message, redirected_to=phone)

        if self._client is None:
            raise RuntimeError("FlowsellClient обязателен при TEST_MODE=false")

        return await self._client.send_message(
            phone=phone,
            text=text,
            channel=channel,
        )

    async def send_pending_messages(self, db: AsyncSession) -> tuple[int, int]:
        if is_quiet_hours_active(settings=self._settings):
            logger.info(
                "quiet hours active, skipping send "
                "(quiet_hours_start=%s quiet_hours_end=%s UTC)",
                self._settings.QUIET_HOURS_START,
                self._settings.QUIET_HOURS_END,
            )
            return 0, 0

        daily_sent = await count_daily_sent(db, self._settings)
        remaining_quota = await remaining_daily_send_quota(db, self._settings)
        if remaining_quota <= 0:
            logger.info(
                "daily send limit reached: daily_sent=%s daily_limit=%s",
                daily_sent,
                self._settings.DAILY_SEND_LIMIT,
            )
            return 0, 0

        batch_limit = min(max(1, self._settings.SEND_PENDING_LIMIT), remaining_quota)
        logger.info(
            "send safeguards: daily_sent=%s daily_limit=%s remaining_quota=%s batch_limit=%s",
            daily_sent,
            self._settings.DAILY_SEND_LIMIT,
            remaining_quota,
            batch_limit,
        )

        if self._settings.TEST_MODE:
            logger.warning(
                "SAFE TEST MODE ENABLED — безопасный режим тестирования; "
                "реальные номера клиентов НЕ используются; "
                "FlowSell отключён; доставка: Telegram (%s) с fallback TEST SENDER; "
                "TEST_RECIPIENTS=%s; TELEGRAM_TEST_CHAT_ID=%s; batch_limit=%s",
                "configured" if self._telegram.is_configured else "not configured",
                self._settings.test_recipient_phones,
                self._settings.TELEGRAM_TEST_CHAT_ID or "(empty)",
                batch_limit,
            )

        logger.info("flowsell: выборка approved-сообщений для отправки (limit=%s)", batch_limit)

        stmt = (
            select(Message)
            .options(selectinload(Message.client))
            .where(Message.status == MessageStatus.approved)
            .order_by(Message.id)
            .limit(batch_limit)
        )
        result = await db.execute(stmt)
        messages = list(result.scalars().all())

        sent = 0
        failed = 0

        for index, message in enumerate(messages):
            if sent >= remaining_quota:
                logger.info(
                    "daily send limit reached: daily_sent=%s daily_limit=%s (during batch)",
                    daily_sent + sent,
                    self._settings.DAILY_SEND_LIMIT,
                )
                break

            phone = self._resolve_phone(message, index)
            if not phone:
                logger.warning(
                    "flowsell: пропуск message_id=%s — нет номера "
                    "(test_mode=%s client_id=%s)",
                    message.id,
                    self._settings.TEST_MODE,
                    message.client_id,
                )
                message.status = MessageStatus.failed
                failed += 1
                continue

            if self._settings.TEST_MODE:
                self._log_test_mode_redirect(message, phone)

            api_result = await self._send_message(
                phone=phone,
                text=message.text,
                channel=message.channel,
                message=message,
            )
            self._apply_result(message, api_result)
            if api_result.ok:
                sent += 1
            else:
                failed += 1

        await db.flush()
        logger.info(
            "flowsell: отправлено=%s ошибок=%s (обработано=%s batch_limit=%s test_mode=%s)",
            sent,
            failed,
            len(messages),
            batch_limit,
            self._settings.TEST_MODE,
        )
        return sent, failed

    def _apply_result(self, message: Message, api_result: FlowsellSendResult) -> None:
        if api_result.ok:
            message.status = MessageStatus.sent
            message.sent_at = datetime.now(timezone.utc)
        else:
            message.status = MessageStatus.failed
            logger.info(
                "flowsell: message_id=%s помечено failed: %s",
                message.id,
                api_result.detail,
            )
