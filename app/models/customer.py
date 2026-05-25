from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PortableUUID


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    anniversary: Mapped[date | None] = mapped_column(Date, nullable=True)
    special_event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    special_event_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    visit_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    total_spent: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        server_default="0.0",
        nullable=False,
    )
    last_visit: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
