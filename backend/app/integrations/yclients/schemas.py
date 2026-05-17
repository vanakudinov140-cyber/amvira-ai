"""Схемы ответов YCLIENTS (минимальный набор полей для синхронизации)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class YclientsEnvelope(BaseModel):
    """Общая обёртка list-эндпоинтов v1."""

    model_config = ConfigDict(extra="allow")

    success: bool = False
    data: list[dict[str, Any]] = Field(default_factory=list)
    meta: dict[str, Any] | list[Any] | None = None


class YclientsBookServicesData(BaseModel):
    """Тело data для GET /book_services/{company_id}."""

    model_config = ConfigDict(extra="allow")

    categories: list[dict[str, Any]] = Field(default_factory=list)
    services: list[dict[str, Any]] = Field(default_factory=list)


class YclientsBookServicesEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    success: bool = False
    data: YclientsBookServicesData | None = None
