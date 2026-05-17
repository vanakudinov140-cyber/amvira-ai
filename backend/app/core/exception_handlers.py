"""Глобальные обработчики ошибок API."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


def _error_payload(message: str) -> dict[str, Any]:
    return {"success": False, "error": message}


def _format_pydantic_errors(errors: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for err in errors[:12]:
        loc = " -> ".join(str(x) for x in err.get("loc", ()))
        parts.append(f"{loc}: {err.get('msg', 'invalid')}")
    return "; ".join(parts) if parts else "Ошибка валидации данных"


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, str):
        msg = detail
    elif isinstance(detail, (list, dict)):
        msg = str(jsonable_encoder(detail))
    else:
        msg = str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(msg),
    )


async def request_validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    msg = _format_pydantic_errors(exc.errors())
    logger.info("request validation error: %s", msg)
    return JSONResponse(
        status_code=422,
        content=_error_payload(msg),
    )


async def pydantic_validation_exception_handler(
    _request: Request,
    exc: ValidationError,
) -> JSONResponse:
    msg = _format_pydantic_errors(exc.errors())
    logger.info("pydantic validation error: %s", msg)
    return JSONResponse(
        status_code=422,
        content=_error_payload(msg),
    )


async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error: %s", exc)
    from app.core.config import get_settings

    settings = get_settings()
    if settings.DEBUG:
        msg = f"{type(exc).__name__}: {exc}"
    else:
        msg = "Внутренняя ошибка сервера"
    return JSONResponse(
        status_code=500,
        content=_error_payload(msg),
    )
