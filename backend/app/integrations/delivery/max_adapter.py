"""Production-safe MAX adapter foundation.

The foundation exposes capabilities, diagnostics, health, and response
normalization. It does not send messages and is not connected to scheduler
execution, background automation, queues, retries, or bulk sends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, get_settings
from app.integrations.delivery.base import (
    DeliveryAdapterCapability,
    DeliveryAdapterHealth,
    DeliveryAdapterPreview,
    DeliveryProviderResponse,
)


@dataclass(frozen=True, slots=True)
class MaxAdapterConfig:
    base_url: str
    access_token_configured: bool
    timeout_seconds: float
    preview_only: bool = True

    def safe_dict(self) -> dict[str, Any]:
        return {
            "base_url_configured": bool(self.base_url),
            "base_url_preview": _redact_url(self.base_url),
            "access_token_configured": self.access_token_configured,
            "timeout_seconds": self.timeout_seconds,
            "preview_only": self.preview_only,
        }


class MaxDeliveryAdapter:
    channel = "max"
    adapter_key = "max"

    def __init__(self, *, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._config = MaxAdapterConfig(
            base_url=getattr(self._settings, "MAX_API_BASE_URL", ""),
            access_token_configured=bool(getattr(self._settings, "MAX_API_TOKEN", "").strip()),
            timeout_seconds=float(getattr(self._settings, "MAX_ADAPTER_TIMEOUT_SECONDS", 5.0)),
        )

    def capability(self) -> DeliveryAdapterCapability:
        configured = self._is_configured
        return DeliveryAdapterCapability(
            channel="max",
            display_name="MAX",
            priority=1,
            configured=configured,
            enabled_for_real_send=False,
            preview_only=True,
            supports_text=True,
            supports_media=False,
            supports_delivery_status=False,
            supports_read_status=False,
            supports_health_check=True,
            max_recipients_per_request=1,
            timeout_seconds=self._config.timeout_seconds,
            notes=[
                "primary delivery channel in business chain",
                "foundation is not wired to real sends",
                "future real sends must require explicit rollout guards",
            ],
        )

    async def health_check(self) -> DeliveryAdapterHealth:
        errors: list[str] = []
        if not self._config.base_url:
            errors.append("MAX_API_BASE_URL is not configured")
        if not self._config.access_token_configured:
            errors.append("MAX_API_TOKEN is not configured")

        return DeliveryAdapterHealth(
            channel="max",
            adapter_key=self.adapter_key,
            state="preview_only" if self._is_configured else "not_configured",
            configured=self._is_configured,
            provider_access=False,
            send_adapter_called=False,
            response_normalized=True,
            timeout_seconds=self._config.timeout_seconds,
            errors=errors,
            diagnostics={
                "config": self._config.safe_dict(),
                "health_check_type": "configuration_only",
                "network_probe": "disabled_for_foundation",
                "real_send_enabled": False,
            },
        )

    def normalize_response(self, raw_response: object | None = None) -> DeliveryProviderResponse:
        if isinstance(raw_response, dict):
            accepted = bool(raw_response.get("accepted") or raw_response.get("ok"))
            provider_message_id = raw_response.get("message_id") or raw_response.get("id")
            raw_status = raw_response.get("status")
            error_code = raw_response.get("error_code")
            error_message = raw_response.get("error_message")
        else:
            accepted = False
            provider_message_id = None
            raw_status = None
            error_code = None
            error_message = None

        return DeliveryProviderResponse(
            channel="max",
            provider_message_id=str(provider_message_id) if provider_message_id else None,
            accepted=accepted,
            status="accepted" if accepted else "preview_only",
            raw_status=raw_status,
            error_code=str(error_code) if error_code else None,
            error_message=str(error_message) if error_message else None,
            retryable=False,
        )

    async def build_preview(self) -> DeliveryAdapterPreview:
        capability = self.capability()
        health = await self.health_check()
        return DeliveryAdapterPreview(
            channel="max",
            adapter_key=self.adapter_key,
            preview_only=True,
            configured=self._is_configured,
            primary_channel=True,
            orchestration_compatible=True,
            provider_access=False,
            send_adapter_called=False,
            background_execution=False,
            cron_execution=False,
            queue_execution=False,
            bulk_execution=False,
            capability=capability,
            health=health,
            normalized_response_example=self.normalize_response({"accepted": True, "message_id": "max-preview"}),
            diagnostics={
                "delivery_chain_position": "primary",
                "fallback_after_failure": "telegram",
                "foundation_scope": "capabilities, diagnostics, health, normalization",
                "real_send_path": "not connected",
            },
            safety_guards=[
                "MAX adapter foundation preview only",
                "no real MAX sends",
                "provider network probes disabled",
                "send adapter is not called",
                "automation state is not changed",
                "no background execution",
                "no cron execution",
                "no queues/workers/retries",
                "no bulk execution",
            ],
        )

    @property
    def _is_configured(self) -> bool:
        return bool(self._config.base_url and self._config.access_token_configured)


def _redact_url(value: str) -> str | None:
    if not value:
        return None
    return value.split("?", 1)[0]
