"""Централизованная настройка логирования приложения."""

from __future__ import annotations

import logging
import os
import sys
from typing import Final

_LOG_FORMAT: Final[str] = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: int | None = None) -> None:
    """
    Единый formatter: время, уровень, имя логгера (модуль), сообщение.
    Уровень: аргумент > переменная окружения LOG_LEVEL > INFO.
    Идемпотентно: повторный вызов не добавляет handlers.
    """

    root = logging.getLogger()
    if root.handlers:
        if level is not None:
            root.setLevel(level)
        return

    resolved = level
    if resolved is None:
        name = (os.getenv("LOG_LEVEL") or "INFO").upper()
        resolved = getattr(logging, name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.NOTSET)
    handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root.setLevel(resolved)
    root.addHandler(handler)

    for noisy in ("uvicorn", "uvicorn.access", "watchfiles"):
        logging.getLogger(noisy).handlers.clear()
        logging.getLogger(noisy).propagate = True
