import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness для Amvera/Docker: без БД и внешних зависимостей."""

    return {"status": "ok"}


@router.get("/health/db")
async def health_db() -> JSONResponse:
    """Readiness: проверка PostgreSQL (не используется платформенным liveness)."""

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        payload = {"status": "ok", "database": "connected"}
        status_code = 200
    except SQLAlchemyError as exc:
        logger.warning("health/db: база недоступна: %s", exc)
        payload = {"status": "degraded", "database": "disconnected"}
        status_code = 503
    except Exception as exc:
        logger.warning("health/db: ошибка подключения: %s", exc)
        payload = {"status": "degraded", "database": "disconnected"}
        status_code = 503

    return JSONResponse(content=payload, status_code=status_code)
