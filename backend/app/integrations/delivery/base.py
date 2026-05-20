"""Shared delivery adapter contracts.

These interfaces are intentionally small and side-effect free for the current
foundation. Future MAX, Telegram, and WhatsApp send adapters can implement the
same contract without changing scheduler orchestration code.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Protocol

DeliveryChannel = Literal["max", "telegram", "whatsapp"]
AdapterState = Literal["ready", "not_configured", "preview_only", "error"]


@dataclass(frozen=True, slots=True)
class DeliveryAdapterCapability:
    channel: DeliveryChannel
    display_name: str
    priority: int
    configured: bool
    enabled_for_real_send: bool
    preview_only: bool
    supports_text: bool
    supports_media: bool
    supports_delivery_status: bool
    supports_read_status: bool
    supports_health_check: bool
    max_recipients_per_request: int
    timeout_seconds: float
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DeliveryAdapterHealth:
    channel: DeliveryChannel
    adapter_key: str
    state: AdapterState
    configured: bool
    provider_access: bool
    send_adapter_called: bool
    response_normalized: bool
    timeout_seconds: float
    errors: list[str] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DeliveryProviderResponse:
    channel: DeliveryChannel
    provider_message_id: str | None
    accepted: bool
    status: str
    raw_status: str | int | None
    error_code: str | None
    error_message: str | None
    retryable: bool
    normalized: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DeliveryAdapterPreview:
    channel: DeliveryChannel
    adapter_key: str
    preview_only: bool
    configured: bool
    primary_channel: bool
    orchestration_compatible: bool
    provider_access: bool
    send_adapter_called: bool
    background_execution: bool
    cron_execution: bool
    queue_execution: bool
    bulk_execution: bool
    capability: DeliveryAdapterCapability
    health: DeliveryAdapterHealth
    normalized_response_example: DeliveryProviderResponse
    diagnostics: dict[str, Any]
    safety_guards: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["capability"] = self.capability.to_dict()
        data["health"] = self.health.to_dict()
        data["normalized_response_example"] = self.normalized_response_example.to_dict()
        return data


class DeliveryAdapter(Protocol):
    channel: DeliveryChannel
    adapter_key: str

    def capability(self) -> DeliveryAdapterCapability:
        """Return static capability information without provider access."""

    async def health_check(self) -> DeliveryAdapterHealth:
        """Return adapter health without sending messages."""

    def normalize_response(self, raw_response: object | None = None) -> DeliveryProviderResponse:
        """Normalize a provider response into a shared delivery response shape."""
