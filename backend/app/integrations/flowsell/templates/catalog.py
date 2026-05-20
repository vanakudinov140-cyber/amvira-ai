"""JSON-backed template catalog for FlowSell delivery."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from importlib import resources
from typing import Any

from app.integrations.flowsell.templates.models import FlowSellTemplate, RenderedTemplate
from app.integrations.flowsell.templates.renderer import extract_placeholders, render_text

logger = logging.getLogger(__name__)

_DEFAULT_TEMPLATE_ID = "default"


class TemplateCatalog:
    """Read-only catalog with event/service-type mapping."""

    def __init__(self, templates: list[FlowSellTemplate]) -> None:
        self._templates = {template.id: template for template in templates if template.enabled}
        self._by_event: dict[str, list[FlowSellTemplate]] = {}
        for template in self._templates.values():
            self._by_event.setdefault(_normalize_key(template.event), []).append(template)
        logger.info("flowsell templates loaded: count=%s", len(self._templates))

    def get(self, template_id: str) -> FlowSellTemplate:
        try:
            return self._templates[template_id]
        except KeyError as exc:
            raise ValueError(f"Unknown FlowSell template: {template_id}") from exc

    def select(self, *, event: str, service_type: str | None = None) -> FlowSellTemplate:
        event_key = _normalize_key(event)
        candidates = self._by_event.get(event_key, [])
        if not candidates:
            raise ValueError(f"No FlowSell templates for event: {event}")

        service_key = _normalize_key(service_type or _DEFAULT_TEMPLATE_ID)
        for template in candidates:
            if service_key and service_key in template.service_types:
                return template

        for template in candidates:
            if _DEFAULT_TEMPLATE_ID in template.service_types:
                return template

        selected = candidates[0]
        logger.warning(
            "flowsell template: no default for event=%s service_type=%s, using=%s",
            event,
            service_type,
            selected.id,
        )
        return selected

    def render(
        self,
        *,
        event: str,
        values: Mapping[str, object | None],
        service_type: str | None = None,
    ) -> RenderedTemplate:
        template = self.select(event=event, service_type=service_type)
        text, missing = render_text(template.text, values)
        if missing:
            logger.info(
                "flowsell template rendered with fallbacks template_id=%s missing=%s",
                template.id,
                missing,
            )
        return RenderedTemplate(
            template_id=template.id,
            category=template.category,
            event=template.event,
            title=template.title,
            text=text,
            missing_placeholders=missing,
        )


def load_template_catalog() -> TemplateCatalog:
    raw = resources.files(__package__).joinpath("catalog.json").read_text(encoding="utf-8")
    data = json.loads(raw)
    templates = [_parse_template(item) for item in data.get("templates", [])]
    if not templates:
        raise ValueError("FlowSell template catalog is empty")
    return TemplateCatalog(templates)


def _parse_template(item: Mapping[str, Any]) -> FlowSellTemplate:
    template_id = _required_str(item, "id")
    text = _required_str(item, "text")
    placeholders = tuple(item.get("placeholders") or extract_placeholders(text))
    return FlowSellTemplate(
        id=template_id,
        category=_required_str(item, "category"),  # type: ignore[arg-type]
        event=_required_str(item, "event"),
        title=_required_str(item, "title"),
        text=text,
        service_types=tuple(_normalize_key(value) for value in item.get("service_types", [])),
        placeholders=placeholders,
        enabled=bool(item.get("enabled", True)),
        version=int(item.get("version", 1)),
    )


def _required_str(item: Mapping[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"FlowSell template requires non-empty {key}")
    return value.strip()


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")
