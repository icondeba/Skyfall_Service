from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PortableUUID


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(),
        ForeignKey("categories.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        nullable=False,
    )
    is_veg: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        nullable=False,
    )
    prep_time_minutes: Mapped[int] = mapped_column(
        Integer,
        default=10,
        server_default="10",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    category: Mapped["Category"] = relationship(back_populates="menu_items")
    variants: Mapped[list["ItemVariant"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
    )
    addons: Mapped[list["ItemAddon"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
    )
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="menu_item")
