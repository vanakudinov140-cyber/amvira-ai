"""Dry-run send orchestration for FlowSell templates.

This module does not call FlowSell API. It prepares and validates a payload
that can later be passed to the real delivery layer after credentials are tested.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from app.integrations.flowsell.mapper import (
    map_retention_channel_to_delivery,
    phone_to_chat_id,
    retention_channel_supported,
)
from app.integrations.flowsell.templates import TemplateCatalog, load_template_catalog

logger = logging.getLogger(__name__)

MAX_FLOWSELL_TEXT_LENGTH = 4096


@dataclass(frozen=True, slots=True)
class FlowSellPayloadPreview:
    event: str
    phone: str
    template: str
    rendered_text: str
    missing_placeholders: list[str]
    dry_run: bool
    service_type: str | None = None
    channel: str = "sms"
    delivery_channel: str = "whatsapp"
    chat_id: str | None = None
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.validation_errors

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["valid"] = self.valid
        return data


class FlowSellSendOrchestrator:
    """Simple event -> template -> render -> payload preview pipeline."""

    def __init__(self, catalog: TemplateCatalog | None = None) -> None:
        self._catalog = catalog or load_template_catalog()

    def render_template(
        self,
        *,
        event: str,
        values: dict[str, object | None],
        service_type: str | None = None,
    ) -> FlowSellPayloadPreview:
        """Render-only preview without phone validation."""
        rendered = self._catalog.render(
            event=event,
            service_type=service_type,
            values=values,
        )
        warnings = _missing_placeholder_warnings(rendered.missing_placeholders)
        preview = FlowSellPayloadPreview(
            event=rendered.event,
            phone="",
            service_type=service_type,
            channel="preview",
            delivery_channel="preview",
            chat_id=None,
            template=rendered.template_id,
            rendered_text=rendered.text,
            missing_placeholders=list(rendered.missing_placeholders),
            validation_warnings=warnings,
            dry_run=True,
        )
        logger.info(
            "flowsell render dry-run event=%s template_id=%s service_type=%s missing=%s",
            preview.event,
            preview.template,
            service_type,
            preview.missing_placeholders,
        )
        return preview

    def build_send_preview(
        self,
        *,
        event: str,
        phone: str,
        values: dict[str, object | None],
        service_type: str | None = None,
        channel: str = "sms",
    ) -> FlowSellPayloadPreview:
        """Build a dry-run payload preview. Does not send anything."""
        rendered = self._catalog.render(
            event=event,
            service_type=service_type,
            values=values,
        )
        delivery_channel = map_retention_channel_to_delivery(channel)
        errors: list[str] = []
        warnings = _missing_placeholder_warnings(rendered.missing_placeholders)
        chat_id: str | None = None

        if not retention_channel_supported(channel):
            errors.append(f"unsupported channel: {channel}")

        try:
            chat_id = phone_to_chat_id(phone)
        except ValueError as exc:
            errors.append(str(exc))

        text = rendered.text.strip()
        if not text:
            errors.append("rendered_text is empty")
        if len(text) > MAX_FLOWSELL_TEXT_LENGTH:
            errors.append(
                f"rendered_text too long: {len(text)} > {MAX_FLOWSELL_TEXT_LENGTH}",
            )
        if not event.strip():
            errors.append("event is required")
        if not phone.strip():
            errors.append("phone is required")

        preview = FlowSellPayloadPreview(
            event=rendered.event,
            phone=phone,
            service_type=service_type,
            channel=channel,
            delivery_channel=delivery_channel,
            chat_id=chat_id,
            template=rendered.template_id,
            rendered_text=text,
            missing_placeholders=list(rendered.missing_placeholders),
            validation_errors=errors,
            validation_warnings=warnings,
            dry_run=True,
        )
        logger.info(
            "flowsell send-preview dry-run event=%s template_id=%s service_type=%s "
            "delivery=%s valid=%s errors=%s warnings=%s",
            preview.event,
            preview.template,
            service_type,
            delivery_channel,
            preview.valid,
            errors,
            warnings,
        )
        return preview


def _missing_placeholder_warnings(placeholders: tuple[str, ...]) -> list[str]:
    return [f"missing placeholder fallback used: {name}" for name in placeholders]
