"""HTTP-клиент YCLIENTS (async httpx)."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Any, Self

import httpx

from app.core.config import Settings
from app.integrations.yclients.exceptions import YclientsApiError, YclientsResponseError
from app.integrations.yclients.schemas import (
    YclientsBookServicesEnvelope,
    YclientsEnvelope,
)

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class YclientsClient:
    """Асинхронный клиент REST API YCLIENTS v1."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._company_id = settings.YCLIENTS_COMPANY_ID
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> Self:
        if not self._settings.YCLIENTS_PARTNER_TOKEN or not self._settings.YCLIENTS_API_KEY:
            raise YclientsApiError(
                "YCLIENTS_PARTNER_TOKEN и YCLIENTS_API_KEY должны быть заданы в окружении",
            )
        if not self._company_id:
            raise YclientsApiError("YCLIENTS_COMPANY_ID должен быть задан в окружении")

        base = self._settings.YCLIENTS_BASE_URL.rstrip("/")
        headers = {
            "Accept": "application/vnd.yclients.v2+json",
            "Content-Type": "application/json",
            "Authorization": (
                f"Bearer {self._settings.YCLIENTS_PARTNER_TOKEN}, "
                f"User {self._settings.YCLIENTS_API_KEY}"
            ),
        }
        self._client = httpx.AsyncClient(
            base_url=base,
            headers=headers,
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
            raise RuntimeError("YclientsClient используйте только внутри async with")
        return self._client

    async def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        client = self._require_client()
        try:
            response = await client.get(path, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = self._short_body(exc.response)
            logger.warning(
                "yclients HTTP error method=GET path=%s status=%s body=%s",
                path,
                status,
                body,
            )
            raise YclientsApiError(
                f"YCLIENTS HTTP {status} для {path}: {body}",
                status_code=status,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("yclients сетевой сбой path=%s: %s", path, exc)
            raise YclientsApiError(f"YCLIENTS сетевой сбой для {path}: {exc}") from exc

        try:
            payload: dict[str, Any] = response.json()
        except ValueError as exc:
            logger.error("yclients некорректный JSON path=%s", path)
            raise YclientsResponseError("YCLIENTS вернул некорректный JSON") from exc

        if not payload.get("success", True):
            logger.warning("yclients success=false path=%s payload=%s", path, payload)
            raise YclientsResponseError(f"YCLIENTS success=false для {path}")

        return payload

    @staticmethod
    def _short_body(response: httpx.Response, limit: int = 500) -> str:
        text = response.text
        if len(text) > limit:
            return f"{text[:limit]}…"
        return text

    async def get_clients(self) -> list[dict[str, Any]]:
        """Список клиентов (GET /clients/{company_id}, постранично)."""
        items: list[dict[str, Any]] = []
        page = 1
        page_size = 200

        while True:
            payload = await self._get_json(
                f"clients/{self._company_id}",
                params={"page": page, "count": page_size},
            )
            env = YclientsEnvelope.model_validate(payload)
            batch = env.data
            if not batch:
                break
            items.extend(batch)
            if len(batch) < page_size:
                break
            page += 1

        logger.info("yclients get_clients: получено %s записей", len(items))
        return items

    async def get_records(self) -> list[dict[str, Any]]:
        """Список записей (GET /records/{company_id}, постранично)."""
        items: list[dict[str, Any]] = []
        page = 1
        page_size = 200

        while True:
            payload = await self._get_json(
                f"records/{self._company_id}",
                params={"page": page, "count": page_size},
            )
            env = YclientsEnvelope.model_validate(payload)
            batch = env.data
            if not batch:
                break
            items.extend(batch)
            if len(batch) < page_size:
                break
            page += 1

        logger.info("yclients get_records: получено %s записей", len(items))
        return items

    async def get_services(self) -> list[dict[str, Any]]:
        """Услуги для бронирования (GET /book_services/{company_id})."""
        payload = await self._get_json(f"book_services/{self._company_id}")
        env = YclientsBookServicesEnvelope.model_validate(payload)
        if env.data is None:
            return []

        category_titles: dict[int, str] = {}
        for cat in env.data.categories:
            cid = cat.get("id")
            if isinstance(cid, int):
                title = cat.get("title")
                if isinstance(title, str):
                    category_titles[cid] = title

        merged: list[dict[str, Any]] = []
        for svc in env.data.services:
            row = dict(svc)
            cat_id = svc.get("category_id")
            if isinstance(cat_id, int) and cat_id in category_titles:
                row["_category_title"] = category_titles[cat_id]
            merged.append(row)

        logger.info("yclients get_services: получено %s услуг", len(merged))
        return merged
