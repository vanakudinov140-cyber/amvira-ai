from __future__ import annotations

from app.core.logging import configure_logging

configure_logging()

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.api.routes.analytics import router as analytics_router
from app.api.routes.scheduler import router as scheduler_router
from app.api.routes.debug import router as debug_router
from app.api.routes.health import router as health_router
from app.api.routes.messages import router as messages_router
from app.api.routes.retention import router as retention_router
from app.api.routes.sync import router as sync_router
from app.api.routes.test_yclients import router as test_yclients_router
from app.core.config import get_settings
from app.core.exception_handlers import (
    http_exception_handler,
    pydantic_validation_exception_handler,
    request_validation_exception_handler,
    unhandled_exception_handler,
)
from app.db.database import engine
from app.scheduler import shutdown_retention_scheduler, start_retention_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    logging.getLogger().setLevel(
        getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )
    logger.info("Приложение запущено: %s", settings.APP_NAME)
    if settings.TEST_MODE:
        logger.warning(
            "SAFE TEST MODE ENABLED — send-pending не шлёт на телефоны клиентов; "
            "TEST_RECIPIENTS=%s",
            settings.test_recipient_phones,
        )

    async def _deferred_startup() -> None:
        # Даём Amvera/Docker успеть получить 200 от /health до фоновых задач.
        await asyncio.sleep(0.5)
        if not settings.SCHEDULER_AUTOMATION_ENABLED:
            logger.info("Scheduler automation disabled (SCHEDULER_AUTOMATION_ENABLED=false)")
        try:
            start_retention_scheduler()
        except Exception:
            logger.exception("Retention scheduler failed to start (non-fatal)")

    startup_task = asyncio.create_task(_deferred_startup())

    yield

    startup_task.cancel()
    with suppress(asyncio.CancelledError):
        await startup_task
    shutdown_retention_scheduler()
    await engine.dispose()
    logger.info("Приложение остановлено")


def create_app() -> FastAPI:
    settings = get_settings()
    logging.getLogger().setLevel(
        getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )

    application = FastAPI(
        title=settings.APP_NAME,
        lifespan=lifespan,
        debug=settings.DEBUG,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.add_exception_handler(HTTPException, http_exception_handler)
    application.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    application.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    application.add_exception_handler(Exception, unhandled_exception_handler)

    application.include_router(health_router)
    application.include_router(sync_router)
    application.include_router(retention_router)
    application.include_router(messages_router)
    application.include_router(test_yclients_router)
    application.include_router(debug_router)
    application.include_router(analytics_router)
    application.include_router(scheduler_router)
    return application


app = create_app()
