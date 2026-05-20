import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=import-error
from app.integrations.flowsell.orchestration import FlowSellSendOrchestrator


def test_send_preview_builds_valid_payload() -> None:
    preview = FlowSellSendOrchestrator().build_send_preview(
        event="appointment_created",
        phone="+7 (999) 123-45-67",
        service_type=None,
        channel="sms",
        values={
            "client_name": "Анна",
            "service_name": "Стрижка",
            "appointment_date": "21 мая",
            "appointment_time": "12:00",
            "master_name": "Мария",
            "booking_link": "https://example.com/booking",
        },
    )

    assert preview.dry_run is True
    assert preview.valid is True
    assert preview.template == "appointment_created_template"
    assert preview.chat_id == "79991234567@c.us"
    assert not preview.validation_errors


def test_send_preview_reports_invalid_phone() -> None:
    preview = FlowSellSendOrchestrator().build_send_preview(
        event="review_request",
        phone="123",
        service_type="brows",
        channel="sms",
        values={"client_name": "Анна", "booking_link": "https://example.com/review"},
    )

    assert preview.valid is False
    assert preview.template == "review_brows_template"
    assert any("Некорректный номер" in error for error in preview.validation_errors)


def test_render_template_uses_missing_placeholder_warnings() -> None:
    preview = FlowSellSendOrchestrator().render_template(
        event="appointment_cancelled",
        values={"client_name": "Анна"},
    )

    assert preview.dry_run is True
    assert preview.template == "appointment_cancelled_template"
    assert "service_name" in preview.missing_placeholders
    assert preview.validation_warnings
