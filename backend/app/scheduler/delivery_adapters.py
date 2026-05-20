"""Read-only delivery adapter status foundation for scheduler admin surfaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.core.config import Settings
from app.integrations.delivery.base import DeliveryAdapterCapability, DeliveryAdapterHealth, DeliveryChannel
from app.integrations.delivery.max_adapter import MaxDeliveryAdapter
from app.scheduler import setup as scheduler_setup
from app.scheduler.delivery_orchestration import CHANNEL_REGISTRY


@dataclass(frozen=True, slots=True)
class DeliveryAdapterStatus:
    channel: str
    adapter_key: str
    priority: int
    configured: bool
    foundation_ready: bool
    real_send_enabled: bool
    orchestration_compatible: bool
    capability: DeliveryAdapterCapability
    health: DeliveryAdapterHealth

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["capability"] = self.capability.to_dict()
        data["health"] = self.health.to_dict()
        return data


@dataclass(frozen=True, slots=True)
class DeliveryAdaptersStatusSnapshot:
    read_only: bool
    adapter_foundation_only: bool
    automation_enabled: bool
    primary_channel: str
    fallback_chain: list[str]
    adapters: list[DeliveryAdapterStatus]
    provider_access: bool
    send_adapter_called: bool
    background_execution: bool
    cron_execution: bool
    queue_execution: bool
    bulk_execution: bool
    safety_guards: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["adapters"] = [adapter.to_dict() for adapter in self.adapters]
        return data


async def build_delivery_adapters_status(
    *,
    settings: Settings | None = None,
) -> DeliveryAdaptersStatusSnapshot:
    max_adapter = MaxDeliveryAdapter(settings=settings)
    max_capability = max_adapter.capability()
    max_health = await max_adapter.health_check()
    registry = list(CHANNEL_REGISTRY)

    adapters = [
        DeliveryAdapterStatus(
            channel="max",
            adapter_key=max_adapter.adapter_key,
            priority=max_capability.priority,
            configured=max_capability.configured,
            foundation_ready=True,
            real_send_enabled=False,
            orchestration_compatible=True,
            capability=max_capability,
            health=max_health,
        ),
        *[_placeholder_status(definition.channel, definition.priority) for definition in registry[1:]],
    ]

    return DeliveryAdaptersStatusSnapshot(
        read_only=True,
        adapter_foundation_only=True,
        automation_enabled=scheduler_setup.is_automation_enabled(),
        primary_channel=registry[0].channel,
        fallback_chain=[definition.channel for definition in registry[1:]],
        adapters=adapters,
        provider_access=False,
        send_adapter_called=False,
        background_execution=False,
        cron_execution=False,
        queue_execution=False,
        bulk_execution=False,
        safety_guards=[
            "adapter status is read-only",
            "MAX adapter foundation only",
            "Telegram adapter interface placeholder only",
            "WhatsApp adapter interface placeholder only",
            "no real adapter sends",
            "provider network probes disabled",
            "automation state is not changed",
            "no background execution",
            "no cron execution",
            "no queues/workers/retries",
            "no bulk execution",
        ],
    )


async def build_max_adapter_preview(
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    preview = await MaxDeliveryAdapter(settings=settings).build_preview()
    return preview.to_dict()


def _placeholder_status(channel: DeliveryChannel, priority: int) -> DeliveryAdapterStatus:
    capability = DeliveryAdapterCapability(
        channel=channel,
        display_name=channel.capitalize(),
        priority=priority,
        configured=False,
        enabled_for_real_send=False,
        preview_only=True,
        supports_text=False,
        supports_media=False,
        supports_delivery_status=False,
        supports_read_status=False,
        supports_health_check=False,
        max_recipients_per_request=1,
        timeout_seconds=0,
        notes=[
            "architecture-ready placeholder",
            "real adapter is not connected in this foundation",
        ],
    )
    health = DeliveryAdapterHealth(
        channel=channel,
        adapter_key=channel,
        state="preview_only",
        configured=False,
        provider_access=False,
        send_adapter_called=False,
        response_normalized=False,
        timeout_seconds=0,
        errors=[f"{channel} adapter is not implemented yet"],
        diagnostics={
            "placeholder": True,
            "real_send_enabled": False,
            "orchestration_position": priority,
        },
    )
    return DeliveryAdapterStatus(
        channel=channel,
        adapter_key=channel,
        priority=priority,
        configured=False,
        foundation_ready=False,
        real_send_enabled=False,
        orchestration_compatible=True,
        capability=capability,
        health=health,
    )
