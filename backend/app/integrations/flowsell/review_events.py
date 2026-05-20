"""Dry-run registry for future delayed review flows.

This module is intentionally not connected to scheduler, queues, or send
execution. It only documents event metadata and service-category matching for
future staging work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ReviewDelayType = Literal["minutes", "days"]
ReviewServiceCategory = Literal[
    "new_client",
    "haircut",
    "coloring",
    "brows",
    "care",
    "makeup",
    "styling",
]


@dataclass(frozen=True, slots=True)
class ReviewEventDefinition:
    event: str
    delay_type: ReviewDelayType
    delay_value: int
    service_category: ReviewServiceCategory
    template_id: str
    enabled_for_automation: bool = False


REVIEW_EVENT_REGISTRY: tuple[ReviewEventDefinition, ...] = (
    ReviewEventDefinition(
        event="review_new_client_60m",
        delay_type="minutes",
        delay_value=60,
        service_category="new_client",
        template_id="review_new_client_60m_template",
    ),
    ReviewEventDefinition(
        event="review_haircut_3d",
        delay_type="days",
        delay_value=3,
        service_category="haircut",
        template_id="review_default_template",
    ),
    ReviewEventDefinition(
        event="review_coloring_3d",
        delay_type="days",
        delay_value=3,
        service_category="coloring",
        template_id="review_coloring_template",
    ),
    ReviewEventDefinition(
        event="review_brows_7d",
        delay_type="days",
        delay_value=7,
        service_category="brows",
        template_id="review_brows_template",
    ),
    ReviewEventDefinition(
        event="review_care_7d",
        delay_type="days",
        delay_value=7,
        service_category="care",
        template_id="review_default_template",
    ),
    ReviewEventDefinition(
        event="review_makeup_7d",
        delay_type="days",
        delay_value=7,
        service_category="makeup",
        template_id="review_default_template",
    ),
    ReviewEventDefinition(
        event="review_styling_7d",
        delay_type="days",
        delay_value=7,
        service_category="styling",
        template_id="review_default_template",
    ),
)

SERVICE_CATEGORY_KEYWORDS: dict[ReviewServiceCategory, tuple[str, ...]] = {
    "haircut": ("стриж", "haircut"),
    "coloring": ("окраш", "color", "colour", "мелирован", "тонирован"),
    "brows": ("бров", "brow", "eyebrow"),
    "care": ("уход", "care", "spa", "спа"),
    "makeup": ("макияж", "makeup", "визаж"),
    "styling": ("уклад", "styling", "локон", "причес", "причёс"),
    "new_client": (),
}


def get_review_event(event: str) -> ReviewEventDefinition:
    normalized = event.strip().lower()
    for definition in REVIEW_EVENT_REGISTRY:
        if definition.event == normalized:
            return definition
    raise ValueError(f"Unknown review event: {event}")


def match_review_service_category(service_name: str) -> ReviewServiceCategory | None:
    normalized = service_name.strip().lower()
    if not normalized:
        return None

    for category, keywords in SERVICE_CATEGORY_KEYWORDS.items():
        if category == "new_client":
            continue
        if any(keyword in normalized for keyword in keywords):
            return category
    return None
