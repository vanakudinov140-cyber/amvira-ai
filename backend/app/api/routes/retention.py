from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import SessionDep, get_messaging_service, get_retention_service
from app.services.messaging.schemas import MessageTemplate, PreviewMessageRequest
from app.services.messaging.service import MessagingService
from app.services.retention.schemas import RetentionCandidatesResponse
from app.services.retention.service import RetentionService

router = APIRouter(prefix="/retention", tags=["retention"])


@router.get("/candidates", response_model=RetentionCandidatesResponse)
async def list_retention_candidates(
    db: SessionDep,
    service: Annotated[RetentionService, Depends(get_retention_service)],
) -> RetentionCandidatesResponse:
    items = await service.get_retention_candidates(db)
    return RetentionCandidatesResponse(count=len(items), items=items)


@router.post("/preview-message", response_model=MessageTemplate)
async def preview_retention_message(
    body: PreviewMessageRequest,
    db: SessionDep,
    retention: Annotated[RetentionService, Depends(get_retention_service)],
    messaging: Annotated[MessagingService, Depends(get_messaging_service)],
) -> MessageTemplate:
    candidates = await retention.get_retention_candidates(db)
    match = next((c for c in candidates if c.client_id == body.client_id), None)
    if match is None:
        raise HTTPException(
            status_code=404,
            detail="Клиент не найден среди retention-кандидатов",
        )
    return messaging.generate_message(match)
