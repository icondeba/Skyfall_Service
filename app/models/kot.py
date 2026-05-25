from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PortableUUID


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class KOT(Base):
    __tablename__ = "kots"
    __table_args__ = (
        CheckConstraint(
            "status IN ('new', 'acknowledged', 'completed')",
            name="ck_kots_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(),
        ForeignKey("orders.id"),
        nullable=False,
    )
    kot_number: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
    )
    items_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="new",
        server_default="new",
        nullable=False,
    )
    printed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    order: Mapped["Order"] = relationship(back_populates="kots")

    @property
    def order_special_instructions(self) -> str | None:
        return self.order.special_instructions if self.order else None
