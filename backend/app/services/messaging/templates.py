"""Текстовые шаблоны retention-сообщений (плейсхолдеры: {client_name}, {procedure_name}, {days_since_visit})."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.services.retention.rules import RetentionAction


@dataclass(frozen=True, slots=True)
class TemplateDefinition:
    title: str
    text: str


TEMPLATES: Final[dict[RetentionAction, TemplateDefinition]] = {
    "monthly_care": TemplateDefinition(
        title="Забота о результате",
        text=(
            "Здравствуйте, {client_name} 🌸\n"
            "После процедуры «{procedure_name}» прошло {days_since_visit} дней.\n"
            "Нежное напоминание: регулярный уход помогает дольше сохранить результат. "
            "Если захотите поддержать эффект — будем рады записать вас."
        ),
    ),
    "gentle_return": TemplateDefinition(
        title="Давно не виделись",
        text=(
            "Здравствуйте, {client_name} 💛\n"
            "Мы заметили, что с последнего визита на «{procedure_name}» "
            "прошло уже {days_since_visit} дней — давно не виделись.\n"
            "Возможно, пора освежить результат — напишите, подберём удобное время."
        ),
    ),
    "comeback_reminder": TemplateDefinition(
        title="Возвращайтесь к нам",
        text=(
            "Здравствуйте, {client_name} ✨\n"
            "По «{procedure_name}» с момента последнего визита прошло {days_since_visit} дней — "
            "вы давно к нам не заходили.\n"
            "Будем рады снова видеть вас в салоне: поможем вернуться к уходу в комфортном ритме."
        ),
    ),
    "winback": TemplateDefinition(
        title="Скучаем по вам",
        text=(
            "Здравствуйте, {client_name} 🤍\n"
            "С последнего визита на «{procedure_name}» прошло {days_since_visit} дней — "
            "мы очень давно вас не видели.\n"
            "Будем искренне рады встретиться снова и помочь вам снова почувствовать себя на высоте."
        ),
    ),
}
