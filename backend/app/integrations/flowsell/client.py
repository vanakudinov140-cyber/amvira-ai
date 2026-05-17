"""HTTP-клиент FlowSell (MVP: одна точка отправки)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = httpx.Timeout(25.0, connect=8.0)


@dataclass(frozen=True, slots=True)
class FlowsellSendResult:
    ok: bool
    detail: str = ""


class FlowsellClient:
    """Асинхронный клиент FlowSell для отправки сообщения."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> Self:
        base = (self._settings.FLOWSELL_API_URL or "").strip()
        key = (self._settings.FLOWSELL_API_KEY or "").strip()
        if not base or not key:
            raise RuntimeError("FLOWSELL_API_URL и FLOWSELL_API_KEY должны быть заданы")

        self._client = httpx.AsyncClient(
            base_url=base.rstrip("/"),
            headers={
                "Authorization": f"Bearer {key}",
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

    async def send_message(self, phone: str, text: str, channel: str) -> FlowsellSendResult:
        """POST /messages — тело MVP; базовый URL задаётся в FLOWSELL_API_URL."""

        client = self._require_client()
        payload: dict[str, Any] = {
            "phone": phone,
            "text": text,
            "channel": channel,
        }
        try:
            response = await client.post("/messages", json=payload)
            response.raise_for_status()
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
            logger.error("flowsell сетевой сбой: %s", exc)
            return FlowsellSendResult(ok=False, detail=str(exc))

        logger.info("flowsell: сообщение принято API status=%s", response.status_code)
        return FlowsellSendResult(ok=True, detail="ok")
