"""Read-only analytics endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import SessionDep, get_analytics_service
from app.services.analytics.service import AnalyticsService
from app.services.feedback.analytics import FeedbackAnalyticsService
from app.services.feedback.attribution import ReturnAttributionService

router = APIRouter(prefix="/analytics", tags=["analytics"])


class ActionsBreakdown(BaseModel):
    monthly_care: int = 0
    gentle_return: int = 0
    comeback_reminder: int = 0
    winback: int = 0


class RetentionOverviewResponse(BaseModel):
    clients_total: int = Field(ge=0)
    retention_candidates: int = Field(ge=0)
    messages_pending: int = Field(ge=0)
    messages_approved: int = Field(ge=0)
    messages_rejected: int = Field(ge=0)
    messages_sent: int = Field(ge=0)
    messages_failed: int = Field(ge=0)
    daily_sent: int = Field(ge=0)
    actions_breakdown: ActionsBreakdown


class TopProcedureItem(BaseModel):
    procedure_name: str
    count: int = Field(ge=0)


class MessagePerformanceResponse(BaseModel):
    prepared_last_24h: int = Field(ge=0)
    sent_last_24h: int = Field(ge=0)
    failed_last_24h: int = Field(ge=0)
    top_procedures: list[TopProcedureItem]


class SchedulerStatusResponse(BaseModel):
    scheduler_running: bool
    last_job_started_at: datetime | None
    last_job_finished_at: datetime | None
    last_job_status: str | None
    last_job_error: str | None


class AutomationSettingsResponse(BaseModel):
    scheduler_running: bool
    automation_enabled: bool
    test_mode: bool
    test_recipients: list[str]
    send_pending_limit: int
    daily_send_limit: int
    quiet_hours_start: int
    quiet_hours_end: int
    last_job_started_at: datetime | None
    last_job_finished_at: datetime | None
    last_job_status: str | None
    last_job_error: str | None


class TopActionItem(BaseModel):
    action: str
    sent: int = Field(ge=0)
    total: int = Field(ge=0)


class AiModerationStats(BaseModel):
    approved: int = Field(ge=0)
    rejected: int = Field(ge=0)
    pending: int = Field(ge=0)


class ModerationInsightsResponse(BaseModel):
    messages_by_segment: dict[str, int]
    return_rate_by_segment: dict[str, float]
    top_performing_actions: list[TopActionItem]
    ai_moderation: AiModerationStats


class ActionPerformanceItem(BaseModel):
    action: str
    sent: int = Field(ge=0)
    returned: int = Field(ge=0)
    return_rate: float = Field(ge=0, le=1)
    revenue: float = Field(ge=0)


class SegmentPerformanceItem(BaseModel):
    segment: str
    sent: int = Field(ge=0)
    returned: int = Field(ge=0)
    return_rate: float = Field(ge=0, le=1)


class EditedPerformanceComparison(BaseModel):
    edited_sent: int = 0
    edited_returned: int = 0
    edited_return_rate: float = 0
    non_edited_sent: int = 0
    non_edited_returned: int = 0
    non_edited_return_rate: float = 0


class RegeneratedPerformanceComparison(BaseModel):
    regenerated_sent: int = 0
    regenerated_returned: int = 0
    regenerated_return_rate: float = 0
    original_sent: int = 0
    original_returned: int = 0
    original_return_rate: float = 0


class AiPerformanceResponse(BaseModel):
    approval_rate: float = Field(ge=0, le=1)
    average_edit_ratio: float = Field(ge=0)
    messages_sent: int = Field(ge=0)
    messages_returned: int = Field(ge=0)
    overall_return_rate: float = Field(ge=0, le=1)
    retention_revenue: float = Field(ge=0)
    top_performing_actions: list[ActionPerformanceItem]
    top_performing_segments: list[SegmentPerformanceItem]
    return_rate_by_action: dict[str, float]
    return_rate_by_segment: dict[str, float]
    edited_vs_original: EditedPerformanceComparison
    regenerated_vs_original: RegeneratedPerformanceComparison
    learning_recommendations: list[str]


@router.get("/retention-overview", response_model=RetentionOverviewResponse)
async def retention_overview(
    db: SessionDep,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> RetentionOverviewResponse:
    data = await service.get_retention_overview(db)
    breakdown = data["actions_breakdown"]
    return RetentionOverviewResponse(
        clients_total=int(data["clients_total"]),
        retention_candidates=int(data["retention_candidates"]),
        messages_pending=int(data["messages_pending"]),
        messages_approved=int(data["messages_approved"]),
        messages_rejected=int(data["messages_rejected"]),
        messages_sent=int(data["messages_sent"]),
        messages_failed=int(data["messages_failed"]),
        daily_sent=int(data["daily_sent"]),
        actions_breakdown=ActionsBreakdown(
            monthly_care=int(breakdown["monthly_care"]),
            gentle_return=int(breakdown["gentle_return"]),
            comeback_reminder=int(breakdown["comeback_reminder"]),
            winback=int(breakdown["winback"]),
        ),
    )


@router.get("/message-performance", response_model=MessagePerformanceResponse)
async def message_performance(
    db: SessionDep,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> MessagePerformanceResponse:
    data = await service.get_message_performance(db)
    return MessagePerformanceResponse(
        prepared_last_24h=int(data["prepared_last_24h"]),
        sent_last_24h=int(data["sent_last_24h"]),
        failed_last_24h=int(data["failed_last_24h"]),
        top_procedures=[
            TopProcedureItem(procedure_name=item["procedure_name"], count=int(item["count"]))
            for item in data["top_procedures"]
        ],
    )


@router.get("/scheduler-status", response_model=SchedulerStatusResponse)
async def scheduler_status(
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> SchedulerStatusResponse:
    data = service.get_scheduler_status()
    return SchedulerStatusResponse(**data)


@router.get("/automation", response_model=AutomationSettingsResponse)
async def automation_settings(
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> AutomationSettingsResponse:
    data = service.get_automation_settings()
    return AutomationSettingsResponse(**data)


@router.get("/moderation-insights", response_model=ModerationInsightsResponse)
async def moderation_insights(
    db: SessionDep,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ModerationInsightsResponse:
    data = await service.get_moderation_insights(db)
    return ModerationInsightsResponse(
        messages_by_segment={k: int(v) for k, v in data["messages_by_segment"].items()},
        return_rate_by_segment={
            k: float(v) for k, v in data["return_rate_by_segment"].items()
        },
        top_performing_actions=[
            TopActionItem(**item) for item in data["top_performing_actions"]
        ],
        ai_moderation=AiModerationStats(**data["ai_moderation"]),
    )


@router.get("/ai-performance", response_model=AiPerformanceResponse)
async def ai_performance(db: SessionDep) -> AiPerformanceResponse:
    try:
        await ReturnAttributionService().attribute_returns(db)
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    data = await FeedbackAnalyticsService().get_ai_performance(db)
    return AiPerformanceResponse(
        approval_rate=float(data["approval_rate"]),
        average_edit_ratio=float(data["average_edit_ratio"]),
        messages_sent=int(data["messages_sent"]),
        messages_returned=int(data["messages_returned"]),
        overall_return_rate=float(data["overall_return_rate"]),
        retention_revenue=float(data["retention_revenue"]),
        top_performing_actions=[
            ActionPerformanceItem(**item) for item in data["top_performing_actions"]
        ],
        top_performing_segments=[
            SegmentPerformanceItem(**item) for item in data["top_performing_segments"]
        ],
        return_rate_by_action={
            k: float(v) for k, v in data["return_rate_by_action"].items()
        },
        return_rate_by_segment={
            k: float(v) for k, v in data["return_rate_by_segment"].items()
        },
        edited_vs_original=EditedPerformanceComparison(**data["edited_vs_original"]),
        regenerated_vs_original=RegeneratedPerformanceComparison(
            **data["regenerated_vs_original"],
        ),
        learning_recommendations=list(data["learning_recommendations"]),
    )
