"""Русские business-friendly подписи для AI UX (без изменения бизнес-логики)."""

from __future__ import annotations

from typing import Any

SEGMENT_LABELS: dict[str, str] = {
    "new": "Новый клиент",
    "active": "Активный",
    "loyal": "Лояльный",
    "sleeping": "Спящий",
    "lost_vip": "VIP без визитов",
    "unknown": "Не определён",
}

ACTION_LABELS: dict[str, str] = {
    "monthly_care": "Ежемесячный уход",
    "gentle_return": "Мягкое возвращение",
    "comeback_reminder": "Напоминание о визите",
    "winback": "Возврат клиента",
}

TRIGGER_LABELS: dict[str, str] = {
    "regular_care": "Пора поддерживающего ухода",
    "moderate_absence": "Заметная пауза между визитами",
    "long_absence": "Длительное отсутствие",
}

ACTION_REASONS: dict[str, str] = {
    "monthly_care": "регулярный уход после недавнего визита",
    "gentle_return": "мягкое напоминание после паузы",
    "comeback_reminder": "клиент давно не был — напоминание о визите",
    "winback": "очень давно не был — сценарий возврата",
}

RETENTION_TRIGGER_LINES: dict[str, str] = {
    "regular_care": "Клиент попал в retention: пора поддерживающего ухода",
    "moderate_absence": "Клиент попал в retention: заметная пауза между визитами",
    "long_absence": "Клиент попал в retention: длительное отсутствие",
}


def label_segment(segment: str | None) -> str:
    if not segment:
        return SEGMENT_LABELS["unknown"]
    return SEGMENT_LABELS.get(segment, segment)


def label_action(action: str | None) -> str:
    if not action:
        return "—"
    return ACTION_LABELS.get(action, action)


def label_trigger_reason(trigger: str | None) -> str:
    if not trigger:
        return TRIGGER_LABELS["long_absence"]
    return TRIGGER_LABELS.get(trigger, trigger)


def retention_trigger_line(trigger: str | None) -> str:
    key = trigger or "long_absence"
    return RETENTION_TRIGGER_LINES.get(
        key,
        "Клиент попал в retention: отсутствие дольше порога",
    )


def enrich_metadata_labels(metadata: dict[str, Any]) -> dict[str, str]:
    segment = str(metadata.get("client_segment") or "unknown")
    action = str(metadata.get("recommended_action") or metadata.get("action") or "")
    trigger = str(metadata.get("trigger_reason") or "long_absence")
    return {
        "client_segment_label": label_segment(segment),
        "recommended_action_label": label_action(action) if action else "—",
        "trigger_reason_label": label_trigger_reason(trigger),
    }
