"""Управление retention automation scheduler."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.scheduler import setup as scheduler_setup

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class SchedulerToggleRequest(BaseModel):
    enabled: bool


class SchedulerToggleResponse(BaseModel):
    success: bool = True
    automation_enabled: bool


class SchedulerRunNowResponse(BaseModel):
    success: bool = True
    message: str = "Retention job triggered"


@router.post("/toggle", response_model=SchedulerToggleResponse)
async def toggle_scheduler(body: SchedulerToggleRequest) -> SchedulerToggleResponse:
    scheduler_setup.set_automation_enabled(body.enabled)
    return SchedulerToggleResponse(automation_enabled=body.enabled)


@router.post("/run-now", response_model=SchedulerRunNowResponse)
async def run_scheduler_now() -> SchedulerRunNowResponse:
    await scheduler_setup.run_retention_job_now()
    return SchedulerRunNowResponse()
