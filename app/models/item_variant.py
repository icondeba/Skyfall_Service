from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PortableUUID


class ItemVariant(Base):
    __tablename__ = "item_variants"

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(),
        ForeignKey("menu_items.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    price_modifier: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        server_default="0.0",
        nullable=False,
    )

    item: Mapped["MenuItem"] = relationship(back_populates="variants")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="variant")
