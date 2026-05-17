"""Pydantic-схемы для retention-анализа."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.services.retention.rules import RetentionAction


class RetentionCandidate(BaseModel):
    client_id: int
    client_name: str
    procedure_name: str
    last_visit_date: date
    days_since_visit: int = Field(ge=0)
    recommended_action: RetentionAction
    recommended_channel: Literal["telegram", "sms"]


class RetentionCandidatesResponse(BaseModel):
    count: int = Field(ge=0)
    items: list[RetentionCandidate]
