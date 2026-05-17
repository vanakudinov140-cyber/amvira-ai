"""Rule-based learning recommendations из накопленного feedback."""

from __future__ import annotations

from typing import Any

from app.i18n.ru import label_action, label_segment


def build_learning_recommendations(stats: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []

    edited = stats.get("edited_vs_original") or {}
    non_edited_rate = float(edited.get("non_edited_return_rate") or 0)
    edited_rate = float(edited.get("edited_return_rate") or 0)
    if edited.get("edited_sent", 0) >= 3 and edited.get("non_edited_sent", 0) >= 3:
        delta = round((edited_rate - non_edited_rate) * 100)
        if delta > 5:
            recommendations.append(
                "Сообщения после ручной корректировки показывают более высокий retention "
                f"(+{delta} п.п. к оригинальному тексту AI).",
            )
        elif delta < -5:
            recommendations.append(
                "Оригинальный текст AI показывает более высокий retention "
                f"(+{abs(delta)} п.п. к отредактированным сообщениям).",
            )

    regen = stats.get("regenerated_vs_original") or {}
    regen_rate = float(regen.get("regenerated_return_rate") or 0)
    orig_rate = float(regen.get("original_return_rate") or 0)
    if regen.get("regenerated_sent", 0) >= 3:
        delta = round((regen_rate - orig_rate) * 100)
        if delta > 5:
            recommendations.append(
                f"Перегенерация AI повышает retention на {delta} п.п. относительно первого варианта.",
            )
        elif delta < -5:
            recommendations.append(
                f"Первый вариант AI эффективнее перегенерации на {abs(delta)} п.п. по retention.",
            )

    by_segment = stats.get("return_rate_by_segment") or {}
    if by_segment:
        best_seg, best_rate = max(by_segment.items(), key=lambda x: float(x[1]))
        if float(best_rate) > 0 and sum(1 for v in by_segment.values() if float(v) > 0) > 1:
            recommendations.append(
                f"Самый эффективный сегмент — «{label_segment(best_seg)}» "
                f"(возврат {int(float(best_rate) * 100)}%).",
            )

    by_action = stats.get("return_rate_by_action") or {}
    if by_action:
        best_action, best_action_rate = max(by_action.items(), key=lambda x: float(x[1]))
        worst_action, worst_action_rate = min(by_action.items(), key=lambda x: float(x[1]))
        if float(best_action_rate) > 0:
            recommendations.append(
                f"Лучший retention-сценарий — «{label_action(best_action)}» "
                f"(возврат {int(float(best_action_rate) * 100)}%).",
            )
        if (
            worst_action != best_action
            and float(worst_action_rate) < float(best_action_rate) * 0.7
            and float(worst_action_rate) >= 0
        ):
            recommendations.append(
                f"Сценарий «{label_action(worst_action)}» отстаёт для текущей базы "
                f"(возврат {int(float(worst_action_rate) * 100)}%). "
                "Стоит пересмотреть формулировки или условия запуска.",
            )

    low_check = stats.get("winback_low_check") or {}
    if low_check.get("sample_size", 0) >= 3:
        rate = float(low_check.get("return_rate") or 0)
        if rate < 0.15:
            recommendations.append(
                "Сценарий «Возврат клиента» слабо работает у клиентов с низким средним чеком — "
                "рассмотрите другой retention-сценарий.",
            )

    approval_rate = float(stats.get("approval_rate") or 0)
    if stats.get("moderation_decisions", 0) >= 5:
        if approval_rate < 0.4:
            recommendations.append(
                "Обнаружена низкая доля одобрений — операторы часто отклоняют тексты AI. "
                "Усильте шаблоны и правила переписывания.",
            )
        elif approval_rate > 0.85:
            recommendations.append(
                "Высокая доля одобрений — текущие AI-сообщения хорошо принимаются операторами.",
            )

    if not recommendations:
        recommendations.append(
            "Накопите больше отправленных сообщений и решений модерации — "
            "появятся персонализированные рекомендации.",
        )

    return recommendations[:6]
