"""Pydantic-схемы для шаблонов сообщений (без отправки)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.services.retention.rules import RetentionAction


class MessageTemplate(BaseModel):
    title: str
    text: str
    action: RetentionAction
    channel: Literal["telegram", "sms"]


class PreviewMessageRequest(BaseModel):
    client_id: int = Field(ge=1)
