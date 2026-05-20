"""Маппинг retention channel / phone → FlowSell WhatsApp API."""

from __future__ import annotations

import re

# FlowSell Flow API на текущем этапе — только WhatsApp (sendMessage).
_FLOWSELL_DELIVERY_CHANNELS = frozenset({"sms", "telegram", "whatsapp", "wa"})


def normalize_phone_digits(phone: str) -> str:
    """Оставляет только цифры; 8XXXXXXXXXX → 7XXXXXXXXXX для РФ."""
    digits = re.sub(r"\D", "", phone.strip())
    if len(digits) == 11 and digits.startswith("8"):
        return "7" + digits[1:]
    return digits


def phone_to_chat_id(phone: str) -> str:
    """
    FlowSell WhatsApp: chatId вида 79001234567@c.us
    https://dev.flowsell.me/docs/api/sending/text/
    """
    digits = normalize_phone_digits(phone)
    if len(digits) < 10:
        raise ValueError(f"Некорректный номер для WhatsApp chatId: {phone!r}")
    return f"{digits}@c.us"


def retention_channel_supported(channel: str) -> bool:
    """Можно ли доставить retention-сообщение через FlowSell (WhatsApp)."""
    return (channel or "").strip().lower() in _FLOWSELL_DELIVERY_CHANNELS


def map_retention_channel_to_delivery(channel: str) -> str:
    """
    Retention хранит telegram/sms; FlowSell шлёт в WhatsApp по номеру телефона.
    Возвращает канал доставки для логов.
    """
    normalized = (channel or "sms").strip().lower()
    if normalized in _FLOWSELL_DELIVERY_CHANNELS:
        return "whatsapp"
    return normalized
