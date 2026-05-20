"""Safe placeholder rendering for FlowSell templates."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping

logger = logging.getLogger(__name__)

PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

DEFAULT_PLACEHOLDER_FALLBACKS: Mapping[str, str] = {
    "client_name": "клиент",
    "service_name": "услуга",
    "appointment_date": "дата записи",
    "appointment_time": "время записи",
    "master_name": "мастер",
    "booking_link": "ссылка для записи",
}


def extract_placeholders(text: str) -> tuple[str, ...]:
    """Return unique placeholders in first-seen order."""
    seen: set[str] = set()
    placeholders: list[str] = []
    for match in PLACEHOLDER_RE.finditer(text):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            placeholders.append(name)
    return tuple(placeholders)


def render_text(
    text: str,
    values: Mapping[str, object | None],
    *,
    fallbacks: Mapping[str, str] = DEFAULT_PLACEHOLDER_FALLBACKS,
) -> tuple[str, tuple[str, ...]]:
    """
    Replace {placeholder} values without eval or a complex template engine.

    Missing values get deterministic fallbacks, and are returned for logging.
    """
    missing: list[str] = []

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        value = values.get(name)
        if value is None or str(value).strip() == "":
            missing.append(name)
            return fallbacks.get(name, "")
        return str(value).strip()

    rendered = PLACEHOLDER_RE.sub(replace, text)
    if missing:
        logger.info("flowsell template render: missing placeholders=%s", sorted(set(missing)))
    return rendered, tuple(dict.fromkeys(missing))
