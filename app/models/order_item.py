from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PortableUUID


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint(
            "item_status IN ('pending', 'preparing', 'ready')",
            name="ck_order_items_item_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(),
        ForeignKey("orders.id"),
        nullable=False,
    )
    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(),
        ForeignKey("menu_items.id"),
        nullable=False,
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(),
        ForeignKey("item_variants.id"),
        nullable=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    addons_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    special_instructions: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    item_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        server_default="pending",
        nullable=False,
    )

    order: Mapped["Order"] = relationship(back_populates="items")
    menu_item: Mapped["MenuItem"] = relationship(back_populates="order_items")
    variant: Mapped["ItemVariant | None"] = relationship(back_populates="order_items")
