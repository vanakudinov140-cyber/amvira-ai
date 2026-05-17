from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MessageStatus

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.message_feedback import MessageFeedback
    from app.models.message_version import MessageVersion


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        index=True,
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[MessageStatus] = mapped_column(
        Enum(
            MessageStatus,
            values_callable=lambda obj: [m.value for m in obj],
            native_enum=False,
        ),
        nullable=False,
        server_default=MessageStatus.pending.value,
    )
    prepared_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    message_metadata: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )

    client: Mapped[Client] = relationship(back_populates="messages")
    versions: Mapped[list[MessageVersion]] = relationship(back_populates="message")
    feedback: Mapped[MessageFeedback | None] = relationship(
        back_populates="message",
        uselist=False,
    )
