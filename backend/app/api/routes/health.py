import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> JSONResponse:
    """Проверка API и подключения к PostgreSQL."""

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        payload = {"status": "ok", "database": "connected"}
        status_code = 200
    except SQLAlchemyError as exc:
        logger.warning("healthcheck: база недоступна: %s", exc)
        payload = {"status": "error", "database": "disconnected"}
        status_code = 503

    return JSONResponse(content=payload, status_code=status_code)
