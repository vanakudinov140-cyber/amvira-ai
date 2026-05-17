from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.procedure import Procedure


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        unique=True,
        index=True,
        doc="Идентификатор записи в YCLIENTS (для синхронизации)",
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        index=True,
        nullable=False,
    )
    procedure_id: Mapped[int] = mapped_column(
        ForeignKey("procedures.id"),
        index=True,
        nullable=False,
    )
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)
    master_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    client: Mapped[Client] = relationship(back_populates="visits")
    procedure: Mapped[Procedure] = relationship(back_populates="visits")
