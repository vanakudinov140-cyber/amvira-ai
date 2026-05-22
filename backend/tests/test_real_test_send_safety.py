import asyncio
import os
import sys

from fastapi import HTTPException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=import-error
from app.api.routes import test_flowsell
from app.api.routes.test_flowsell import FlowSellSendPreviewBody
from app.core.config import Settings
from app.integrations.flowsell.send_adapter import FlowSellControlledSendResult


def _settings() -> Settings:
    return Settings(
        TEST_MODE=True,
        TEST_RECIPIENTS="79504744246",
        ALLOW_TEST_RECIPIENTS=True,
        MAX_TEST_SEND=1,
        TEST_COOLDOWN_SECONDS=10,
        FLOWSELL_DRY_RUN=True,
        FLOWSELL_INSTANCE_ID="123",
        FLOWSELL_API_KEY="token",
    )


def _body(phone: str = "79504744246") -> FlowSellSendPreviewBody:
    return FlowSellSendPreviewBody(
        event="reminder_24h",
        phone=phone,
        channel="sms",
        values={
            "client_name": "Анна",
            "service_name": "Окрашивание",
            "appointment_date": "Завтра",
            "appointment_time": "14:30",
            "master_name": "Мария",
            "booking_link": "демо",
        },
    )


def _reset_counters() -> None:
    setattr(test_flowsell, "_test_send_count", 0)
    setattr(test_flowsell, "_test_last_send_at", None)


def test_real_test_send_rejects_non_allowlisted_phone(monkeypatch) -> None:
    _reset_counters()
    monkeypatch.setattr(test_flowsell, "get_settings", _settings)

    async def run() -> None:
        try:
            await test_flowsell.flowsell_send_real(_body("79990000000"))
        except HTTPException as exc:
            assert exc.status_code == 403
            assert exc.detail == "Отправка разрешена только на тестовые номера"
        else:
            raise AssertionError("non-allowlisted recipient must be blocked")

    asyncio.run(run())


def test_real_test_send_forces_single_preview_payload_send(monkeypatch) -> None:
    _reset_counters()
    monkeypatch.setattr(test_flowsell, "get_settings", _settings)

    class FakeAdapter:
        def __init__(self, *, settings: Settings) -> None:
            assert settings.FLOWSELL_DRY_RUN is False
            assert settings.TEST_MODE is False

        async def send_event(self, **kwargs):
            assert kwargs["phone"] == "79504744246"
            assert kwargs["event"] == "reminder_24h"
            assert kwargs["values"]["client_name"] == "Анна"
            return FlowSellControlledSendResult(
                dry_run=False,
                sent=True,
                provider="flowsell",
                event="reminder_24h",
                template="reminder_24h_template",
                rendered_text="preview text",
                phone="79504744246",
                chat_id="79504744246@c.us",
                message_id="msg-1",
                channel="sms",
            )

    monkeypatch.setattr(test_flowsell, "FlowSellSendAdapter", FakeAdapter)

    async def run() -> None:
        result = await test_flowsell.flowsell_send_real(_body())
        assert result.sent is True
        assert result.status == "sent"
        assert result.message_id == "msg-1"
        assert getattr(test_flowsell, "_test_send_count") == 1

    asyncio.run(run())
