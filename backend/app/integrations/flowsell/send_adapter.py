"""Controlled real-send adapter for FlowSell.

The adapter is safe by default: FLOWSELL_DRY_RUN=true means no provider calls.
It is intentionally not connected to scheduler, moderation, or bulk sends.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.config import Settings, get_settings
from app.integrations.flowsell.client import FlowsellClient
from app.integrations.flowsell.exceptions import FlowsellNotConfiguredError
from app.integrations.flowsell.orchestration import (
    FlowSellPayloadPreview,
    FlowSellSendOrchestrator,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FlowSellControlledSendResult:
    dry_run: bool
    sent: bool
    provider: str
    event: str
    template: str
    rendered_text: str
    phone: str
    chat_id: str | None
    message_id: str | None = None
    service_type: str | None = None
    channel: str = "sms"
    validation_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    provider_response_preview: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FlowSellSendAdapter:
    """Single-message controlled adapter around orchestration + FlowSellClient."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        orchestrator: FlowSellSendOrchestrator | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._orchestrator = orchestrator or FlowSellSendOrchestrator()

    async def send_event(
        self,
        *,
        event: str,
        phone: str,
        values: dict[str, object | None],
        service_type: str | None = None,
        channel: str = "sms",
    ) -> FlowSellControlledSendResult:
        """
        Build payload and optionally send a single message.

        Real send happens only when all safety gates pass:
        FLOWSELL_DRY_RUN=false, TEST_MODE=false, FlowSell credentials configured,
        and validation has no errors.
        """
        preview = self._orchestrator.build_send_preview(
            event=event,
            phone=phone,
            values=values,
            service_type=service_type,
            channel=channel,
        )
        warnings = list(preview.validation_warnings)
        dry_run = bool(self._settings.FLOWSELL_DRY_RUN)

        if dry_run:
            warnings.append("FLOWSELL_DRY_RUN=true: provider call skipped")
            return self._result_from_preview(preview, dry_run=True, warnings=warnings)

        if self._settings.TEST_MODE:
            warnings.append("TEST_MODE=true: real FlowSell send is blocked")
            logger.warning(
                "flowsell controlled-send blocked by TEST_MODE event=%s template_id=%s",
                preview.event,
                preview.template,
            )
            return self._result_from_preview(preview, dry_run=False, warnings=warnings)

        if not self._settings.flowsell_configured:
            warnings.append("FlowSell credentials are not configured")
            logger.warning(
                "flowsell controlled-send skipped: credentials missing event=%s template_id=%s",
                preview.event,
                preview.template,
            )
            return self._result_from_preview(preview, dry_run=False, warnings=warnings)

        if preview.validation_errors:
            logger.warning(
                "flowsell controlled-send validation failed event=%s template_id=%s errors=%s",
                preview.event,
                preview.template,
                preview.validation_errors,
            )
            return self._result_from_preview(preview, dry_run=False, warnings=warnings)

        logger.info(
            "flowsell controlled-send provider=%s dry_run=false event=%s template_id=%s "
            "chat_id=%s warnings=%s",
            "flowsell",
            preview.event,
            preview.template,
            preview.chat_id,
            warnings,
        )

        try:
            async with FlowsellClient(self._settings) as client:
                provider_result = await client.send_message(
                    phone=preview.phone,
                    text=preview.rendered_text,
                    channel=preview.channel,
                )
        except FlowsellNotConfiguredError as exc:
            warnings.append(str(exc))
            logger.warning("flowsell controlled-send config error: %s", exc)
            return self._result_from_preview(preview, dry_run=False, warnings=warnings)

        logger.info(
            "flowsell controlled-send finished sent=%s idMessage=%s detail=%s",
            provider_result.ok,
            provider_result.id_message,
            provider_result.detail[:200],
        )
        return FlowSellControlledSendResult(
            dry_run=False,
            sent=provider_result.ok,
            provider="flowsell",
            event=preview.event,
            service_type=preview.service_type,
            channel=preview.channel,
            template=preview.template,
            rendered_text=preview.rendered_text,
            phone=preview.phone,
            chat_id=preview.chat_id,
            message_id=provider_result.id_message,
            validation_errors=preview.validation_errors,
            warnings=warnings,
            provider_response_preview=provider_result.detail[:500],
        )

    @staticmethod
    def _result_from_preview(
        preview: FlowSellPayloadPreview,
        *,
        dry_run: bool,
        warnings: list[str],
    ) -> FlowSellControlledSendResult:
        logger.info(
            "flowsell controlled-send preview provider=flowsell dry_run=%s event=%s "
            "template_id=%s chat_id=%s errors=%s warnings=%s",
            dry_run,
            preview.event,
            preview.template,
            preview.chat_id,
            preview.validation_errors,
            warnings,
        )
        return FlowSellControlledSendResult(
            dry_run=dry_run,
            sent=False,
            provider="flowsell",
            event=preview.event,
            service_type=preview.service_type,
            channel=preview.channel,
            template=preview.template,
            rendered_text=preview.rendered_text,
            phone=preview.phone,
            chat_id=preview.chat_id,
            validation_errors=preview.validation_errors,
            warnings=warnings,
        )
