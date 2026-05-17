"""Правила отбора retention-кандидатов (без отправки сообщений)."""

from __future__ import annotations

from typing import Literal

# YCLIENTS attendance: 1 — клиент пришёл, услуги оказаны (завершённый визит).
COMPLETED_ATTENDANCE_VALUES: frozenset[int] = frozenset({1})

DEFAULT_REMINDER_MIN_DAYS = 30

RetentionAction = Literal[
    "monthly_care",
    "gentle_return",
    "comeback_reminder",
    "winback",
]


def is_completed_visit(attendance: int | None) -> bool:
    return attendance in COMPLETED_ATTENDANCE_VALUES


def reminder_min_days_threshold(reminder_min_days: int | None) -> int:
    """COALESCE(reminder_min_days, 30) для MVP без настройки процедур."""
    if reminder_min_days is None:
        return DEFAULT_REMINDER_MIN_DAYS
    return reminder_min_days


def is_retention_eligible(days_since_visit: int, reminder_min_days: int | None) -> bool:
    return days_since_visit >= reminder_min_days_threshold(reminder_min_days)


def recommend_action(days_since_visit: int) -> RetentionAction:
    """Сегментация сообщения по давности последнего визита."""

    if days_since_visit >= 365:
        return "winback"
    if days_since_visit >= 120:
        return "comeback_reminder"
    if days_since_visit >= 60:
        return "gentle_return"
    return "monthly_care"


def recommend_channel(telegram: str | None) -> Literal["telegram", "sms"]:
    """Канал доставки: Telegram при наличии username/идентификатора, иначе SMS."""

    if telegram and telegram.strip():
        return "telegram"
    return "sms"
