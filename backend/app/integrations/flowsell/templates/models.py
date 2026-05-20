"""Small data models for FlowSell templates.

These models are intentionally DB-ready but do not require migrations yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

TemplateCategory = Literal[
    "reminders",
    "reviews",
    "appointment_created",
    "appointment_rescheduled",
    "appointment_cancelled",
    "aftercare",
]


@dataclass(frozen=True, slots=True)
class FlowSellTemplate:
    id: str
    category: TemplateCategory
    event: str
    title: str
    text: str
    service_types: tuple[str, ...] = field(default_factory=tuple)
    placeholders: tuple[str, ...] = field(default_factory=tuple)
    enabled: bool = True
    version: int = 1


@dataclass(frozen=True, slots=True)
class RenderedTemplate:
    template_id: str
    category: TemplateCategory
    event: str
    title: str
    text: str
    missing_placeholders: tuple[str, ...] = field(default_factory=tuple)
