import pytest

from app.integrations.flowsell.mapper import phone_to_chat_id, retention_channel_supported


def test_phone_to_chat_id_ru() -> None:
    assert phone_to_chat_id("8 (900) 123-45-67") == "79001234567@c.us"


def test_phone_to_chat_id_international() -> None:
    assert phone_to_chat_id("+79001234567") == "79001234567@c.us"


def test_phone_invalid() -> None:
    with pytest.raises(ValueError):
        phone_to_chat_id("123")


def test_retention_channel_supported() -> None:
    assert retention_channel_supported("sms")
    assert retention_channel_supported("telegram")
    assert not retention_channel_supported("email")
