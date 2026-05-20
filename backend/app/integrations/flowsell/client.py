"""HTTP-клиент FlowSell Flow API (WhatsApp sendMessage)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self

import httpx

from app.core.config import Settings
from app.integrations.flowsell.exceptions import FlowsellNotConfiguredError
from app.integrations.flowsell.mapper import map_retention_channel_to_delivery, phone_to_chat_id

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = httpx.Timeout(25.0, connect=8.0)
_DEFAULT_BASE_URL = "https://dev.flowsell.me/api/v1"


@dataclass(frozen=True, slots=True)
class FlowsellSendResult:
    ok: bool
    detail: str = ""
    id_message: str | None = None


class FlowsellClient:
    """
    Асинхронный клиент FlowSell WhatsApp API.

    Документация: https://dev.flowsell.me/docs/
    Отправка текста: POST /waInstance{idInstance}/sendMessage/{apiTokenInstance}
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    @staticmethod
    def _resolve_credentials(settings: Settings) -> tuple[str, str, str]:
        instance_id = (settings.FLOWSELL_INSTANCE_ID or "").strip()
        api_token = (settings.FLOWSELL_API_KEY or "").strip()
        base_url = (settings.FLOWSELL_API_BASE_URL or _DEFAULT_BASE_URL).strip().rstrip("/")

        if not instance_id or not api_token:
            raise FlowsellNotConfiguredError(
                "Задайте FLOWSELL_INSTANCE_ID и FLOWSELL_API_KEY "
                "(idInstance и apiTokenInstance из кабинета FlowSell).",
            )
        return base_url, instance_id, api_token

    async def __aenter__(self) -> Self:
        base_url, _, _ = self._resolve_credentials(self._settings)
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=_DEFAULT_TIMEOUT,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _require_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("FlowsellClient только внутри async with")
        return self._client

    def _parse_api_payload(self, data: Any) -> FlowsellSendResult:
        if not isinstance(data, dict):
            return FlowsellSendResult(ok=False, detail=f"unexpected response: {data!r}")

        if "code" in data and "description" in data:
            code = data.get("code")
            desc = str(data.get("description", ""))
            return FlowsellSendResult(
                ok=False,
                detail=f"API {code}: {desc}",
            )

        id_message = data.get("idMessage")
        if id_message:
            return FlowsellSendResult(ok=True, detail="ok", id_message=str(id_message))

        return FlowsellSendResult(ok=False, detail=f"unexpected response: {data}")

    async def send_message(self, phone: str, text: str, channel: str) -> FlowsellSendResult:
        """
        Отправка текстового WhatsApp-сообщения.

        retention `channel` (sms/telegram) маппится на WhatsApp-доставку по номеру.
        """
        base_url, instance_id, api_token = self._resolve_credentials(self._settings)
        delivery = map_retention_channel_to_delivery(channel)

        try:
            chat_id = phone_to_chat_id(phone)
        except ValueError as exc:
            logger.warning("flowsell: invalid phone=%s channel=%s: %s", phone, channel, exc)
            return FlowsellSendResult(ok=False, detail=str(exc))

        path = f"/waInstance{instance_id}/sendMessage/{api_token}"
        payload = {"chatId": chat_id, "message": text}

        client = self._require_client()
        logger.info(
            "flowsell send: delivery=%s retention_channel=%s chatId=%s len=%s",
            delivery,
            channel,
            chat_id,
            len(text),
        )

        try:
            response = await client.post(path, json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500]
            logger.warning(
                "flowsell HTTP error status=%s body=%s",
                exc.response.status_code,
                body,
            )
            return FlowsellSendResult(
                ok=False,
                detail=f"HTTP {exc.response.status_code}: {body}",
            )
        except httpx.RequestError as exc:
            logger.error("flowsell network error: %s", exc)
            return FlowsellSendResult(ok=False, detail=str(exc))
        except ValueError as exc:
            logger.warning("flowsell invalid JSON: %s", exc)
            return FlowsellSendResult(ok=False, detail=f"invalid JSON: {exc}")

        result = self._parse_api_payload(data)
        if result.ok:
            logger.info(
                "flowsell send ok idMessage=%s base_url=%s",
                result.id_message,
                base_url,
            )
        else:
            logger.warning("flowsell send failed: %s", result.detail)
        return result

    async def check_whatsapp(self, phone: str) -> FlowsellSendResult:
        """POST checkWhatsapp — есть ли WhatsApp на номере."""
        _, instance_id, api_token = self._resolve_credentials(self._settings)
        try:
            digits = phone_to_chat_id(phone).split("@", 1)[0]
            phone_number = int(digits)
        except ValueError as exc:
            return FlowsellSendResult(ok=False, detail=str(exc))

        path = f"/waInstance{instance_id}/checkWhatsapp/{api_token}"
        client = self._require_client()
        try:
            response = await client.post(path, json={"phoneNumber": phone_number})
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.warning("flowsell checkWhatsapp error: %s", exc)
            return FlowsellSendResult(ok=False, detail=str(exc))

        if isinstance(data, dict) and data.get("existsWhatsapp") is True:
            return FlowsellSendResult(ok=True, detail="exists")
        return FlowsellSendResult(ok=False, detail=str(data))
