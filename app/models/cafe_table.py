from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PortableUUID


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class CafeTable(Base):
    __tablename__ = "cafe_tables"
    __table_args__ = (
        CheckConstraint(
            "status IN ('free', 'occupied', 'reserved', 'bill_requested')",
            name="ck_cafe_tables_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    table_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    qr_code_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default="free",
        server_default="free",
        nullable=False,
    )
    capacity: Mapped[int] = mapped_column(
        Integer,
        default=4,
        server_default="4",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    orders: Mapped[list["Order"]] = relationship(back_populates="table")
