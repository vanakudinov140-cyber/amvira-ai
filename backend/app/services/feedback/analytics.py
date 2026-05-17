"""AI effectiveness analytics на основе message_feedback."""

from __future__ import annotations

import logging
from collections import defaultdict
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MessageStatus, MessageVersionSource
from app.models.message import Message
from app.models.message_feedback import MessageFeedback
from app.models.message_version import MessageVersion
from app.services.feedback.learning import build_learning_recommendations

logger = logging.getLogger(__name__)


class FeedbackAnalyticsService:
    async def get_ai_performance(self, db: AsyncSession) -> dict[str, Any]:
        logger.info("feedback analytics: calculating ai-performance")

        stmt = (
            select(Message, MessageFeedback)
            .outerjoin(MessageFeedback, MessageFeedback.message_id == Message.id)
        )
        rows = (await db.execute(stmt)).all()

        approved_count = 0
        rejected_count = 0
        edited_ratios: list[float] = []
        sent_total = 0
        returned_total = 0
        revenue_total = Decimal("0")

        by_action: dict[str, dict[str, int]] = defaultdict(lambda: {"sent": 0, "returned": 0})
        by_segment: dict[str, dict[str, int]] = defaultdict(lambda: {"sent": 0, "returned": 0})
        by_action_revenue: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

        edited_stats = {"edited_sent": 0, "edited_returned": 0, "non_edited_sent": 0, "non_edited_returned": 0}
        regen_stats = {"regenerated_sent": 0, "regenerated_returned": 0, "original_sent": 0, "original_returned": 0}

        message_ids = [m.id for m, _ in rows]
        regen_ids: set[int] = set()
        if message_ids:
            regen_rows = await db.execute(
                select(MessageVersion.message_id)
                .where(
                    MessageVersion.message_id.in_(message_ids),
                    MessageVersion.source == MessageVersionSource.regenerate,
                )
                .distinct(),
            )
            regen_ids = {r[0] for r in regen_rows.all()}

        for message, feedback in rows:
            if feedback is None:
                continue

            if feedback.approved_by_operator is True:
                approved_count += 1
            elif feedback.approved_by_operator is False:
                rejected_count += 1

            if feedback.manually_edited and float(feedback.edited_ratio or 0) > 0:
                edited_ratios.append(float(feedback.edited_ratio))

            if message.status != MessageStatus.sent:
                continue

            sent_total += 1
            action = message.action
            segment = "unknown"
            if isinstance(message.message_metadata, dict):
                segment = str(message.message_metadata.get("client_segment") or "unknown")
                avg_check = float(message.message_metadata.get("average_check") or 0)
            else:
                avg_check = 0.0

            returned = bool(feedback.client_returned)
            if returned:
                returned_total += 1
                revenue_total += Decimal(str(feedback.revenue_after_return or 0))

            by_action[action]["sent"] += 1
            by_segment[segment]["sent"] += 1
            if returned:
                by_action[action]["returned"] += 1
                by_segment[segment]["returned"] += 1
                by_action_revenue[action] += Decimal(str(feedback.revenue_after_return or 0))

            if feedback.manually_edited:
                edited_stats["edited_sent"] += 1
                if returned:
                    edited_stats["edited_returned"] += 1
            else:
                edited_stats["non_edited_sent"] += 1
                if returned:
                    edited_stats["non_edited_returned"] += 1

            if message.id in regen_ids:
                regen_stats["regenerated_sent"] += 1
                if returned:
                    regen_stats["regenerated_returned"] += 1
            else:
                regen_stats["original_sent"] += 1
                if returned:
                    regen_stats["original_returned"] += 1

        moderation_decisions = approved_count + rejected_count
        approval_rate = (
            approved_count / moderation_decisions if moderation_decisions else 0.0
        )
        avg_edit_ratio = (
            sum(edited_ratios) / len(edited_ratios) if edited_ratios else 0.0
        )
        overall_return_rate = returned_total / sent_total if sent_total else 0.0

        return_rate_by_action = {
            action: (data["returned"] / data["sent"] if data["sent"] else 0.0)
            for action, data in by_action.items()
        }
        return_rate_by_segment = {
            seg: (data["returned"] / data["sent"] if data["sent"] else 0.0)
            for seg, data in by_segment.items()
        }

        top_actions = sorted(
            [
                {
                    "action": action,
                    "sent": data["sent"],
                    "returned": data["returned"],
                    "return_rate": data["returned"] / data["sent"] if data["sent"] else 0.0,
                    "revenue": float(by_action_revenue[action]),
                }
                for action, data in by_action.items()
            ],
            key=lambda x: (x["return_rate"], x["revenue"]),
            reverse=True,
        )[:5]

        top_segments = sorted(
            [
                {
                    "segment": seg,
                    "sent": data["sent"],
                    "returned": data["returned"],
                    "return_rate": data["returned"] / data["sent"] if data["sent"] else 0.0,
                }
                for seg, data in by_segment.items()
            ],
            key=lambda x: x["return_rate"],
            reverse=True,
        )[:5]

        edited_vs_original = {
            "edited_sent": edited_stats["edited_sent"],
            "edited_returned": edited_stats["edited_returned"],
            "edited_return_rate": (
                edited_stats["edited_returned"] / edited_stats["edited_sent"]
                if edited_stats["edited_sent"]
                else 0.0
            ),
            "non_edited_sent": edited_stats["non_edited_sent"],
            "non_edited_returned": edited_stats["non_edited_returned"],
            "non_edited_return_rate": (
                edited_stats["non_edited_returned"] / edited_stats["non_edited_sent"]
                if edited_stats["non_edited_sent"]
                else 0.0
            ),
        }

        regenerated_vs_original = {
            "regenerated_sent": regen_stats["regenerated_sent"],
            "regenerated_returned": regen_stats["regenerated_returned"],
            "regenerated_return_rate": (
                regen_stats["regenerated_returned"] / regen_stats["regenerated_sent"]
                if regen_stats["regenerated_sent"]
                else 0.0
            ),
            "original_sent": regen_stats["original_sent"],
            "original_returned": regen_stats["original_returned"],
            "original_return_rate": (
                regen_stats["original_returned"] / regen_stats["original_sent"]
                if regen_stats["original_sent"]
                else 0.0
            ),
        }

        winback_low = {"sample_size": 0, "returned": 0, "return_rate": 0.0}
        for message, feedback in rows:
            if message.status != MessageStatus.sent or feedback is None:
                continue
            if message.action != "winback":
                continue
            meta = message.message_metadata if isinstance(message.message_metadata, dict) else {}
            if float(meta.get("average_check") or 0) >= 5000:
                continue
            winback_low["sample_size"] += 1
            if feedback.client_returned:
                winback_low["returned"] += 1
        if winback_low["sample_size"]:
            winback_low["return_rate"] = winback_low["returned"] / winback_low["sample_size"]

        stats_for_learning = {
            "approval_rate": approval_rate,
            "moderation_decisions": moderation_decisions,
            "edited_vs_original": edited_vs_original,
            "regenerated_vs_original": regenerated_vs_original,
            "return_rate_by_segment": return_rate_by_segment,
            "return_rate_by_action": return_rate_by_action,
            "winback_low_check": winback_low,
        }

        return {
            "approval_rate": round(approval_rate, 3),
            "average_edit_ratio": round(avg_edit_ratio, 2),
            "messages_sent": sent_total,
            "messages_returned": returned_total,
            "overall_return_rate": round(overall_return_rate, 3),
            "retention_revenue": float(revenue_total),
            "top_performing_actions": top_actions,
            "top_performing_segments": top_segments,
            "return_rate_by_action": return_rate_by_action,
            "return_rate_by_segment": return_rate_by_segment,
            "edited_vs_original": edited_vs_original,
            "regenerated_vs_original": regenerated_vs_original,
            "learning_recommendations": build_learning_recommendations(stats_for_learning),
        }
