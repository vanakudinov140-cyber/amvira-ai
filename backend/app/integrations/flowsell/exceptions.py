"""Ошибки интеграции FlowSell."""

from __future__ import annotations


class FlowsellError(Exception):
    """Базовая ошибка FlowSell."""


class FlowsellNotConfiguredError(FlowsellError):
    """Нет idInstance / apiTokenInstance в настройках."""


class FlowsellDeliveryError(FlowsellError):
    """Ошибка отправки или ответ API с code/description."""

    def __init__(self, message: str, *, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code
