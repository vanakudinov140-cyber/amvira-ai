"""MVP explainability: metadata + human-readable reasoning для retention messages."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.i18n.ru import (
    ACTION_REASONS,
    enrich_metadata_labels,
    label_action,
    label_segment,
    retention_trigger_line,
)
from app.services.retention.rules import RetentionAction
from app.services.segmentation.service import SegmentationService, is_high_average_check
from app.services.segmentation.schemas import ClientSegment

_TRIGGER_BY_ACTION: dict[RetentionAction, str] = {
    "monthly_care": "regular_care",
    "gentle_return": "moderate_absence",
    "comeback_reminder": "long_absence",
    "winback": "long_absence",
}


class ExplainabilityService:
    def __init__(self, segmentation: SegmentationService | None = None) -> None:
        self._segmentation = segmentation or SegmentationService()

    async def build_metadata_for_client(
        self,
        db: AsyncSession,
        *,
        client_id: int,
        action: str,
        days_since_visit: int | None = None,
    ) -> dict[str, Any]:
        profile = await self._segmentation.get_client_visit_profile(db, client_id)
        if profile is None:
            action_typed: RetentionAction = action  # type: ignore[assignment]
            metadata: dict[str, Any] = {
                "days_since_last_visit": days_since_visit or 0,
                "previous_visit_frequency_days": None,
                "average_check": 0,
                "visit_count": 0,
                "client_segment": "new",
                "trigger_reason": _TRIGGER_BY_ACTION.get(action_typed, "long_absence"),
                "predicted_return_probability": 0.35,
                "recommended_action": action,
            }
            metadata.update(enrich_metadata_labels(metadata))
            return metadata

        days = days_since_visit if days_since_visit is not None else profile.days_since_last_visit
        action_typed: RetentionAction = action  # type: ignore[assignment]

        probability = self._predict_return_probability(
            segment=profile.segment,
            days_since_last=days,
            frequency_days=profile.previous_visit_frequency_days,
        )

        metadata = {
            "days_since_last_visit": days,
            "previous_visit_frequency_days": profile.previous_visit_frequency_days,
            "average_check": round(profile.average_check, 2),
            "visit_count": profile.visit_count,
            "client_segment": profile.segment,
            "trigger_reason": _TRIGGER_BY_ACTION.get(action_typed, "long_absence"),
            "predicted_return_probability": probability,
            "recommended_action": action,
        }
        metadata.update(enrich_metadata_labels(metadata))
        return metadata

    def build_explain_lines(self, metadata: dict[str, Any]) -> list[str]:
        days = int(metadata.get("days_since_last_visit") or 0)
        freq = metadata.get("previous_visit_frequency_days")
        segment = str(metadata.get("client_segment") or "unknown")
        action = str(metadata.get("recommended_action") or metadata.get("action") or "")
        avg_check = float(metadata.get("average_check") or 0)
        probability = float(metadata.get("predicted_return_probability") or 0)

        lines = [
            f"Клиент не приходил {days} дн.",
        ]

        if freq:
            lines.append(f"Раньше посещал примерно каждые {freq} дн.")
        elif int(metadata.get("visit_count") or 0) <= 1:
            lines.append("Пока мало истории визитов для оценки частоты")

        if avg_check > 0:
            check_label = "высокий" if is_high_average_check(avg_check) else "средний"
            lines.append(f"Средний чек {int(avg_check):,} ₽ ({check_label})".replace(",", " "))

        lines.append(f"Сегмент клиента: {label_segment(segment)}")
        if action:
            reason = ACTION_REASONS.get(action, "retention-сценарий")
            lines.append(f"Сценарий: {label_action(action)} — {reason}")

        lines.append(
            f"Оценка вероятности возврата: {int(probability * 100)}%",
        )
        lines.append(retention_trigger_line(str(metadata.get("trigger_reason") or "long_absence")))
        return lines

    @staticmethod
    def _predict_return_probability(
        *,
        segment: ClientSegment,
        days_since_last: int,
        frequency_days: int | None,
    ) -> float:
        score = 0.45
        segment_boost = {
            "loyal": 0.18,
            "active": 0.12,
            "new": 0.05,
            "sleeping": -0.08,
            "lost_vip": 0.1,
        }
        score += segment_boost.get(segment, 0)

        if frequency_days and frequency_days > 0:
            ratio = days_since_last / frequency_days
            if ratio <= 1.2:
                score += 0.12
            elif ratio <= 2.0:
                score += 0.04
            else:
                score -= 0.06

        return round(max(0.05, min(0.95, score)), 2)
