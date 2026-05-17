from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.message import Message


class MessageFeedback(Base):
    __tablename__ = "message_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    approved_by_operator: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    manually_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    edited_ratio: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, server_default="0")
    client_returned: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    return_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    revenue_after_return: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    message: Mapped[Message] = relationship(back_populates="feedback")
