from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Record(Base):
    __tablename__ = "records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    yclients_record_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    client_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    staff_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    service_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    record_datetime: Mapped[datetime | None] = mapped_column(
        "datetime",
        DateTime(timezone=True),
        nullable=True,
    )
    attendance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    save_sum: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
