from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_db
from app.integrations.flowsell.client import FlowsellClient
from app.integrations.flowsell.service import FlowsellService
from app.integrations.yclients.client import YclientsClient
from app.integrations.yclients.service import YclientsSyncService
from app.services.analytics.service import AnalyticsService
from app.services.messaging.moderation_service import ModerationService
from app.services.messaging.service import MessagingService
from app.services.retention.service import RetentionService
from app.services.message_preparation.service import MessagePreparationService

SessionDep = Annotated[AsyncSession, Depends(get_db)]


async def get_yclients_client() -> AsyncGenerator[YclientsClient, None]:
    async with YclientsClient(get_settings()) as client:
        yield client


def get_yclients_sync_service(
    client: Annotated[YclientsClient, Depends(get_yclients_client)],
) -> YclientsSyncService:
    return YclientsSyncService(client)


def get_messaging_service() -> MessagingService:
    return MessagingService()


def get_moderation_service() -> ModerationService:
    return ModerationService()


def get_retention_service() -> RetentionService:
    return RetentionService()


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()


def get_message_preparation_service(
    retention: Annotated[RetentionService, Depends(get_retention_service)],
    messaging: Annotated[MessagingService, Depends(get_messaging_service)],
) -> MessagePreparationService:
    return MessagePreparationService(retention, messaging)


async def get_flowsell_client() -> AsyncGenerator[FlowsellClient | None, None]:
    settings = get_settings()
    if settings.TEST_MODE:
        yield None
        return

    if not settings.flowsell_configured:
        raise HTTPException(
            status_code=503,
            detail=(
                "FlowSell не настроен: задайте FLOWSELL_INSTANCE_ID и FLOWSELL_API_KEY "
                "(idInstance и apiTokenInstance из кабинета FlowSell)"
            ),
        )
    async with FlowsellClient(settings) as client:
        yield client


def get_flowsell_service(
    client: Annotated[FlowsellClient | None, Depends(get_flowsell_client)],
) -> FlowsellService:
    return FlowsellService(client, get_settings())