import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=import-error
from app.core.config import Settings
from app.integrations.flowsell.send_adapter import FlowSellSendAdapter


def _values() -> dict[str, object | None]:
    return {
        "client_name": "Анна",
        "service_name": "Стрижка",
        "appointment_date": "21 мая",
        "appointment_time": "12:00",
        "master_name": "Мария",
        "booking_link": "https://example.com/booking",
    }


def test_send_adapter_defaults_to_dry_run() -> None:
    async def run() -> None:
        settings = Settings(TEST_MODE=True, TEST_RECIPIENTS="79990000000")
        result = await FlowSellSendAdapter(settings=settings).send_event(
            event="appointment_created",
            phone="79991234567",
            values=_values(),
        )

        assert result.dry_run is True
        assert result.sent is False
        assert result.template == "appointment_created_template"
        assert any("FLOWSELL_DRY_RUN=true" in warning for warning in result.warnings)

    asyncio.run(run())


def test_send_adapter_blocks_real_send_when_test_mode_enabled() -> None:
    async def run() -> None:
        settings = Settings(
            TEST_MODE=True,
            TEST_RECIPIENTS="79990000000",
            FLOWSELL_DRY_RUN=False,
            FLOWSELL_INSTANCE_ID="123",
            FLOWSELL_API_KEY="token",
        )
        result = await FlowSellSendAdapter(settings=settings).send_event(
            event="appointment_created",
            phone="79991234567",
            values=_values(),
        )

        assert result.dry_run is False
        assert result.sent is False
        assert any("TEST_MODE=true" in warning for warning in result.warnings)

    asyncio.run(run())


def test_send_adapter_gracefully_handles_missing_credentials() -> None:
    async def run() -> None:
        settings = Settings(
            TEST_MODE=False,
            FLOWSELL_DRY_RUN=False,
            FLOWSELL_INSTANCE_ID="",
            FLOWSELL_API_KEY="",
        )
        result = await FlowSellSendAdapter(settings=settings).send_event(
            event="appointment_created",
            phone="79991234567",
            values=_values(),
        )

        assert result.dry_run is False
        assert result.sent is False
        assert any("credentials" in warning.lower() for warning in result.warnings)

    asyncio.run(run())
