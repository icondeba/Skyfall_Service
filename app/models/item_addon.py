from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PortableUUID


class ItemAddon(Base):
    __tablename__ = "item_addons"

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(),
        ForeignKey("menu_items.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    extra_price: Mapped[float] = mapped_column(Float, nullable=False)
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        nullable=False,
    )

    item: Mapped["MenuItem"] = relationship(back_populates="addons")
