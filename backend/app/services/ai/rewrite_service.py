"""AI rewrite layer для retention-сообщений (MVP: mock provider)."""

from __future__ import annotations

import logging
import re

from app.core.config import Settings, get_settings
from app.services.retention.rules import RetentionAction

logger = logging.getLogger(__name__)

_FORBIDDEN_FRAGMENTS = (
    "скидк",
    "акци",
    "бесплат",
    "промокод",
    "гарантиру",
    "лечени",
    "диагноз",
    "100%",
)

_GREETINGS = (
    "Здравствуйте, {client_name} 🌸",
    "Добрый день, {client_name} ✨",
    "Привет, {client_name} 💛",
)

_CLOSINGS: dict[RetentionAction, tuple[str, ...]] = {
    "monthly_care": (
        "Если захотите поддержать эффект — мы рядом ✨",
        "Будем рады видеть вас снова ✨",
        "Можно снова освежить образ — напишите, когда удобно ✨",
    ),
    "gentle_return": (
        "Если захотите обновить результат — мы рядом ✨",
        "Будем рады снова вас видеть — подберём удобное время ✨",
        "Напишите, когда захотите освежить образ ✨",
    ),
    "comeback_reminder": (
        "Будем рады видеть вас снова ✨",
        "Будем рады снова вас видеть в салоне ✨",
        "Если захотите вернуться к уходу — мы рядом ✨",
    ),
    "winback": (
        "Будем искренне рады встретиться снова ✨",
        "Будем рады видеть вас снова ✨",
        "Если захотите снова заглянуть к нам — будем рады ✨",
    ),
}

_MIDDLE_LINES: dict[RetentionAction, tuple[str, ...]] = {
    "monthly_care": (
        "После «{procedure_name}» прошло {days_since_visit} дней — небольшое напоминание про регулярный уход.",
        "С момента визита на «{procedure_name}» прошло {days_since_visit} дней: бережный уход помогает сохранить результат.",
    ),
    "gentle_return": (
        "С последнего визита на «{procedure_name}» прошло {days_since_visit} дней — давно не виделись.",
        "По «{procedure_name}» уже {days_since_visit} дней с прошлого визита — давно вас не было у нас.",
    ),
    "comeback_reminder": (
        "По «{procedure_name}» прошло {days_since_visit} дней — вы давно к нам не заходили.",
        "С последнего визита на «{procedure_name}» прошло {days_since_visit} дней, будем рады снова вас видеть.",
    ),
    "winback": (
        "С последнего визита на «{procedure_name}» прошло {days_since_visit} дней — мы очень давно вас не видели.",
        "По «{procedure_name}» уже {days_since_visit} дней — давно не были у нас.",
    ),
}


def _stable_index(seed: str, size: int) -> int:
    if size <= 0:
        return 0
    return sum(ord(ch) for ch in seed) % size


class RewriteService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def rewrite_retention_message(
        self,
        *,
        original_text: str,
        client_name: str,
        procedure_name: str,
        action: RetentionAction,
        days_since_visit: int,
        client_id: int | None = None,
    ) -> str:
        if not self._settings.AI_REWRITE_ENABLED:
            return original_text

        try:
            if self._settings.AI_PROVIDER == "mock":
                rewritten = self._mock_rewrite(
                    client_name=client_name,
                    procedure_name=procedure_name,
                    action=action,
                    days_since_visit=days_since_visit,
                )
            else:
                logger.warning(
                    "AI rewrite: неизвестный provider=%s, используем original",
                    self._settings.AI_PROVIDER,
                )
                return original_text

            self._validate_rewrite(
                rewritten,
                procedure_name=procedure_name,
                days_since_visit=days_since_visit,
            )
            logger.info(
                "AI rewrite applied: client_id=%s action=%s provider=%s",
                client_id,
                action,
                self._settings.AI_PROVIDER,
            )
            return rewritten
        except Exception:
            logger.exception(
                "AI rewrite failed: client_id=%s action=%s",
                client_id,
                action,
            )
            logger.info(
                "AI rewrite fallback used: client_id=%s action=%s",
                client_id,
                action,
            )
            return original_text

    def _mock_rewrite(
        self,
        *,
        client_name: str,
        procedure_name: str,
        action: RetentionAction,
        days_since_visit: int,
    ) -> str:
        seed = f"{client_name}|{procedure_name}|{days_since_visit}|{action}"
        greeting = _GREETINGS[_stable_index(seed + ":g", len(_GREETINGS))].format(
            client_name=client_name,
        )
        middle_pool = _MIDDLE_LINES[action]
        middle = middle_pool[_stable_index(seed + ":m", len(middle_pool))].format(
            procedure_name=procedure_name,
            days_since_visit=days_since_visit,
        )
        closing_pool = _CLOSINGS[action]
        closing = closing_pool[_stable_index(seed + ":c", len(closing_pool))]

        # Порядок фраз варьируется (перестановка middle/closing визуально)
        if _stable_index(seed + ":order", 2) == 0:
            body = f"{middle}\n{closing}"
        else:
            body = f"{closing}\n{middle}"

        return f"{greeting}\n{body}"

    @staticmethod
    def _validate_rewrite(
        rewritten: str,
        *,
        procedure_name: str,
        days_since_visit: int,
    ) -> None:
        text = rewritten.strip()
        if not text or len(text) > 600:
            raise ValueError("rewrite: недопустимая длина текста")

        lowered = text.lower()
        for fragment in _FORBIDDEN_FRAGMENTS:
            if fragment in lowered:
                raise ValueError(f"rewrite: запрещённый фрагмент «{fragment}»")

        if procedure_name not in text:
            raise ValueError("rewrite: в тексте должна остаться процедура")

        if str(days_since_visit) not in text:
            raise ValueError("rewrite: в тексте должно остаться число дней")

        if re.search(r"\d+\s*%", text):
            raise ValueError("rewrite: запрещены процентные обещания")
