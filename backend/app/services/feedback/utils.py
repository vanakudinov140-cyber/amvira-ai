from __future__ import annotations

from difflib import SequenceMatcher


def compute_edited_ratio(original: str, edited: str) -> float:
    """Доля изменения текста в процентах (0 = без изменений, 100 = полностью новый)."""
    original = (original or "").strip()
    edited = (edited or "").strip()
    if not original and not edited:
        return 0.0
    if not original:
        return 100.0
    ratio = SequenceMatcher(None, original, edited).ratio()
    return round((1.0 - ratio) * 100.0, 2)


def original_ai_text_from_metadata(metadata: dict | None) -> str | None:
    if not metadata:
        return None
    value = metadata.get("original_ai_text")
    return str(value) if value else None
