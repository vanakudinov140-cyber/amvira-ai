"""Перечисления для ORM."""



from __future__ import annotations



from enum import Enum





class MessageStatus(str, Enum):

    """Статус retention-сообщения (модерация → отправка)."""



    pending = "pending"

    approved = "approved"

    rejected = "rejected"

    sent = "sent"

    failed = "failed"


class MessageVersionSource(str, Enum):
    ai = "ai"
    manual = "manual"
    regenerate = "regenerate"


