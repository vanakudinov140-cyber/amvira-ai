import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.integrations.flowsell.templates import load_template_catalog
from app.integrations.flowsell.templates.renderer import extract_placeholders, render_text


def test_extract_placeholders_unique_order() -> None:
    assert extract_placeholders("{client_name} {service_name} {client_name}") == (
        "client_name",
        "service_name",
    )


def test_render_text_uses_fallbacks_for_missing_values() -> None:
    rendered, missing = render_text(
        "Здравствуйте, {client_name}. Запись: {appointment_date} в {appointment_time}.",
        {"client_name": "Анна", "appointment_date": None},
    )

    assert "Анна" in rendered
    assert "дата записи" in rendered
    assert "время записи" in rendered
    assert missing == ("appointment_date", "appointment_time")


def test_catalog_selects_event_default_template() -> None:
    catalog = load_template_catalog()

    rendered = catalog.render(
        event="appointment_created",
        values={
            "client_name": "Анна",
            "service_name": "Стрижка",
            "appointment_date": "21 мая",
            "appointment_time": "12:00",
            "master_name": "Мария",
            "booking_link": "https://example.com/booking",
        },
    )

    assert rendered.template_id == "appointment_created_template"
    assert "Стрижка" in rendered.text
    assert not rendered.missing_placeholders


def test_catalog_maps_service_type_to_review_template() -> None:
    catalog = load_template_catalog()

    rendered = catalog.render(
        event="review_request",
        service_type="hair_coloring",
        values={"client_name": "Анна", "booking_link": "https://example.com/review"},
    )

    assert rendered.template_id == "review_coloring_template"


def test_catalog_falls_back_to_default_template() -> None:
    catalog = load_template_catalog()

    rendered = catalog.render(
        event="review_request",
        service_type="unknown_service",
        values={"client_name": "Анна", "service_name": "Маникюр"},
    )

    assert rendered.template_id == "review_default_template"
    assert "ссылка для записи" in rendered.text
