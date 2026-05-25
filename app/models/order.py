from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PortableUUID


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'preparing', 'ready', 'served', 'cancelled')",
            name="ck_orders_status",
        ),
        CheckConstraint(
            "order_type IN ('dine_in', 'takeaway')",
            name="ck_orders_order_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    table_id: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(),
        ForeignKey("cafe_tables.id"),
        nullable=True,
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(),
        ForeignKey("customers.id"),
        nullable=True,
    )
    placed_by_staff_id: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(),
        ForeignKey("staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        server_default="pending",
        nullable=False,
    )
    order_type: Mapped[str] = mapped_column(
        String(20),
        default="dine_in",
        server_default="dine_in",
        nullable=False,
    )
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Float, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Float, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    special_instructions: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    table: Mapped["CafeTable | None"] = relationship(back_populates="orders")
    customer: Mapped["Customer | None"] = relationship(back_populates="orders")
    placed_by_staff: Mapped["Staff | None"] = relationship(foreign_keys=[placed_by_staff_id])
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    kots: Mapped[list["KOT"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    invoice: Mapped["Invoice | None"] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        uselist=False,
    )
