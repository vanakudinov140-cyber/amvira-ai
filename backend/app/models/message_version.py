from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MessageVersionSource

if TYPE_CHECKING:
    from app.models.message import Message


class MessageVersion(Base):
    __tablename__ = "message_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    old_content: Mapped[str] = mapped_column(Text, nullable=False)
    new_content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[MessageVersionSource] = mapped_column(
        Enum(
            MessageVersionSource,
            values_callable=lambda obj: [m.value for m in obj],
            native_enum=False,
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    message: Mapped[Message] = relationship(back_populates="versions")
