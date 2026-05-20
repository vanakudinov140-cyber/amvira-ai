import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=import-error
from app.integrations.flowsell.review_events import (
    REVIEW_EVENT_REGISTRY,
    get_review_event,
    match_review_service_category,
)
from app.integrations.flowsell.templates import load_template_catalog


def test_review_event_registry_contains_delayed_foundation_events() -> None:
    registry = {definition.event: definition for definition in REVIEW_EVENT_REGISTRY}

    assert set(registry) == {
        "review_new_client_60m",
        "review_haircut_3d",
        "review_coloring_3d",
        "review_brows_7d",
        "review_care_7d",
        "review_makeup_7d",
        "review_styling_7d",
    }
    assert registry["review_new_client_60m"].delay_type == "minutes"
    assert registry["review_new_client_60m"].delay_value == 60
    assert registry["review_haircut_3d"].delay_type == "days"
    assert registry["review_haircut_3d"].delay_value == 3
    assert registry["review_brows_7d"].delay_value == 7
    assert all(not definition.enabled_for_automation for definition in REVIEW_EVENT_REGISTRY)


def test_review_event_registry_template_ids_exist_in_catalog() -> None:
    catalog = load_template_catalog()

    for definition in REVIEW_EVENT_REGISTRY:
        assert catalog.get(definition.template_id)


def test_review_event_lookup_and_service_category_matching() -> None:
    assert get_review_event("review_coloring_3d").service_category == "coloring"
    assert match_review_service_category("Сложное окрашивание волос") == "coloring"
    assert match_review_service_category("Женская стрижка") == "haircut"
    assert match_review_service_category("Коррекция бровей") == "brows"
    assert match_review_service_category("Уход для волос") == "care"
    assert match_review_service_category("Вечерний макияж") == "makeup"
    assert match_review_service_category("Укладка локоны") == "styling"
    assert match_review_service_category("") is None


def test_review_service_category_matching_real_salon_names() -> None:
    examples = {
        "Стрижка женская": "haircut",
        "Женская стрижка": "haircut",
        "Окрашивание волос": "coloring",
        "Окрашивание в один тон": "coloring",
        "Архитектура бровей": "brows",
        "Уход для волос": "care",
        "Вечерний макияж": "makeup",
        "Укладка волос": "styling",
    }

    for service_name, expected_category in examples.items():
        assert match_review_service_category(service_name) == expected_category
