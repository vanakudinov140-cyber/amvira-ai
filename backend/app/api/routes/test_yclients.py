"""Временные тестовые эндпоинты (не для production)."""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["test"])

_YCLIENTS_AUTH_URL = "https://api.yclients.com/api/v1/auth"


class YclientsAuthTestBody(BaseModel):
    login: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


@router.post("/yclients-auth", response_model=None)
async def yclients_auth_probe(body: YclientsAuthTestBody) -> Response:
    """
    Прокси к POST https://api.yclients.com/api/v1/auth (только partner token).
    Ответ тела YCLIENTS возвращается как есть (тот же HTTP status).
    """

    settings = get_settings()
    partner = (settings.YCLIENTS_PARTNER_TOKEN or "").strip()
    if not partner:
        raise HTTPException(
            status_code=400,
            detail="YCLIENTS_PARTNER_TOKEN не задан в окружении",
        )

    headers = {
        "Accept": "application/vnd.yclients.v2+json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {partner}",
    }
    payload = {"login": body.login, "password": body.password}

    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            _YCLIENTS_AUTH_URL,
            headers=headers,
            json=payload,
        )

    logger.info(
        "test yclients-auth: status=%s",
        response.status_code,
    )

    try:
        data = response.json()
    except ValueError:
        return Response(
            content=response.content,
            status_code=response.status_code,
            media_type=response.headers.get("content-type", "application/octet-stream"),
        )

    return JSONResponse(status_code=response.status_code, content=data)
