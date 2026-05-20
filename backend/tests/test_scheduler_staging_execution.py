import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=import-error
from app.core.config import Settings
from app.integrations.flowsell.send_adapter import FlowSellControlledSendResult
from app.scheduler.staging_execution import (
    StagingExecutionInput,
    StagingRealSendInput,
    build_staging_execution_preview,
    execute_staging_real_send_test,
)


def _settings(
    *,
    dry_run: bool = True,
    test_mode: bool = True,
    test_recipients: str = "79990000000",
) -> Settings:
    return Settings(
        TEST_MODE=test_mode,
        TEST_RECIPIENTS=test_recipients,
        FLOWSELL_DRY_RUN=dry_run,
        DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/db",
    )


def test_staging_execution_preview_runs_one_record_without_provider_access() -> None:
    result = build_staging_execution_preview(
        StagingExecutionInput(
            flow_type="review",
            service_name="Стрижка женская",
            record_id="demo-record-1",
            client_phone="79991234567",
            is_new_client=False,
            client_name="Анна",
            appointment_date="20.05.2026",
            appointment_time="12:00",
            master_name="Мария",
            booking_link="https://example.com/review",
        ),
        settings=_settings(),
    )

    assert result.dry_run is True
    assert result.dry_run_confirmed is True
    assert result.provider_blocked is True
    assert result.provider_access is False
    assert result.send_adapter_called is False
    assert result.send_pipeline_called is False
    assert result.background_execution is False
    assert result.matched_category == "haircut"
    assert result.matched_event == "review_haircut_3d"
    assert result.template_id == "review_haircut_template"
    assert result.recipient_used == "79990000000"
    assert result.rendered_text_preview is not None
    assert "Анна" in result.rendered_text_preview
    assert "Стрижка женская" in result.rendered_text_preview
    assert result.send_payload_preview is not None
    assert result.send_payload_preview.template == "review_haircut_template"
    assert result.send_payload_preview.phone == "79990000000"
    assert result.normalized_chat_id == "79990000000@c.us"
    assert result.template_used == "review_haircut_template"
    assert result.render_status == "rendered"
    assert result.payload_validation_status == "valid"
    assert result.would_be_sent is True
    assert result.provider_block_reason == "flowsell_dry_run_enabled"
    assert result.final_dry_run_stop_stage == "dry_run_provider_block"
    assert result.execution_timeline == [
        "scenario_matched",
        "template_selected",
        "text_rendered",
        "payload_prepared",
        "checks_passed",
        "send_blocked_by_dry_run",
    ]
    assert result.simulated_whatsapp_payload is not None
    assert result.simulated_whatsapp_payload.chat_id == "79990000000@c.us"
    assert result.simulated_whatsapp_payload.channel == "whatsapp"
    assert result.simulated_whatsapp_payload.provider == "flowsell"
    assert "Анна" in result.simulated_whatsapp_payload.message
    assert result.send_payload_preview.delivery_channel == "whatsapp"
    assert result.send_payload_preview.valid is True
    assert "send_payload_build" in result.execution_steps_completed
    assert "provider_blocked" in result.execution_steps_completed


def test_staging_execution_preview_blocks_when_dry_run_is_disabled() -> None:
    result = build_staging_execution_preview(
        StagingExecutionInput(
            flow_type="review",
            service_name="Стрижка женская",
            is_new_client=False,
        ),
        settings=_settings(dry_run=False),
    )

    assert result.dry_run_confirmed is False
    assert result.provider_blocked is True
    assert result.provider_access is False
    assert result.send_adapter_called is False
    assert result.send_pipeline_called is False
    assert result.background_execution is False
    assert result.rendered_text_preview is None
    assert result.send_payload_preview is None
    assert result.simulated_whatsapp_payload is None
    assert result.would_be_sent is False
    assert result.provider_block_reason == "safety_guard_before_provider"
    assert result.final_dry_run_stop_stage == "blocked_before_payload_build"
    assert any("FLOWSELL_DRY_RUN" in error for error in result.guard_errors)


def test_staging_execute_preview_endpoint_is_manual_and_dry_run_only(monkeypatch) -> None:
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("TEST_RECIPIENTS", "79990000000")
    monkeypatch.setenv("FLOWSELL_DRY_RUN", "true")

    from fastapi.testclient import TestClient

    from app.core.config import get_settings
    from app.main import app

    get_settings.cache_clear()
    client = TestClient(app)
    response = client.post(
        "/scheduler/staging-execute-preview",
        json={
            "flow_type": "review",
            "service_name": "Стрижка женская",
            "client_phone": "79991234567",
            "record_id": "demo-record-1",
            "is_new_client": False,
            "client_name": "Анна",
        },
    )
    data = response.json()

    assert response.status_code == 200
    assert data["matched_category"] == "haircut"
    assert data["matched_event"] == "review_haircut_3d"
    assert data["template_id"] == "review_haircut_template"
    assert data["recipient_used"] == "79990000000"
    assert data["dry_run_confirmed"] is True
    assert data["provider_blocked"] is True
    assert data["provider_access"] is False
    assert data["send_adapter_called"] is False
    assert data["send_pipeline_called"] is False
    assert data["background_execution"] is False
    assert data["send_payload_preview"]["valid"] is True
    assert data["normalized_chat_id"] == "79990000000@c.us"
    assert data["template_used"] == "review_haircut_template"
    assert data["render_status"] == "rendered"
    assert data["payload_validation_status"] == "valid"
    assert data["would_be_sent"] is True
    assert data["provider_block_reason"] == "flowsell_dry_run_enabled"
    assert data["final_dry_run_stop_stage"] == "dry_run_provider_block"
    assert data["simulated_whatsapp_payload"]["chat_id"] == "79990000000@c.us"
    assert data["simulated_whatsapp_payload"]["provider"] == "flowsell"


def test_staging_execution_preview_page_is_human_friendly() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/scheduler/staging-execution-preview")
    text = response.text

    assert response.status_code == 200
    assert "Staging-проверка исполнения" in text
    assert "Только staging проверка" in text
    assert "Реальных отправок нет" in text
    assert "Провайдер отключён" in text
    assert "Таймлайн исполнения" in text
    assert "Симулированные данные WhatsApp" in text
    assert "Было бы готово к отправке" in text
    assert "/scheduler/staging-execute-preview" in text
    assert "<pre" not in text.lower()


def test_staging_real_send_requires_confirmation_and_dry_run_disabled() -> None:
    result = asyncio.run(
        execute_staging_real_send_test(
            StagingRealSendInput(
                flow_type="review",
                service_name="Стрижка женская",
                confirm_real_send=False,
            ),
            settings=_settings(dry_run=True),
        ),
    )

    assert result.blocked is True
    assert result.send_adapter_called is False
    assert any("confirm_real_send" in error for error in result.guard_errors)
    assert any("FLOWSELL_DRY_RUN" in error for error in result.guard_errors)


def test_staging_real_send_calls_adapter_once_for_test_recipient(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeAdapter:
        def __init__(self, *, settings: Settings) -> None:
            self._settings = settings

        async def send_event(self, **kwargs: object) -> FlowSellControlledSendResult:
            calls.append(kwargs)
            return FlowSellControlledSendResult(
                dry_run=False,
                sent=True,
                provider="flowsell",
                event=str(kwargs["event"]),
                template="review_haircut_template",
                rendered_text="Анна, спасибо за визит на Стрижка женская!",
                phone=str(kwargs["phone"]),
                chat_id="79990000000@c.us",
                message_id="test-message-id",
                service_type=str(kwargs["service_type"]),
                channel=str(kwargs["channel"]),
                provider_response_preview='{"idMessage":"test-message-id"}',
            )

    monkeypatch.setattr(
        "app.scheduler.staging_execution.FlowSellSendAdapter",
        FakeAdapter,
    )

    result = asyncio.run(
        execute_staging_real_send_test(
            StagingRealSendInput(
                flow_type="review",
                service_name="Стрижка женская",
                confirm_real_send=True,
                client_name="Анна",
            ),
            settings=_settings(dry_run=False, test_mode=False),
        ),
    )

    assert len(calls) == 1
    assert calls[0]["phone"] == "79990000000"
    assert calls[0]["event"] == "review_request"
    assert result.blocked is False
    assert result.sent is True
    assert result.dry_run is False
    assert result.send_adapter_called is True
    assert result.background_execution is False
    assert result.bulk_execution is False
    assert result.message_id == "test-message-id"
    assert result.provider_diagnostics is not None
    assert result.provider_diagnostics.provider_accepted is True
    assert result.provider_diagnostics.connection_state == "not_configured"
    assert result.provider_diagnostics.delivery_status == "unavailable"
