from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PortableUUID


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(),
        ForeignKey("orders.id"),
        unique=True,
        nullable=False,
    )
    billed_by_staff_id: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(),
        ForeignKey("staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    whatsapp_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
    )
    sms_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    order: Mapped["Order"] = relationship(back_populates="invoice")
    billed_by_staff: Mapped["Staff | None"] = relationship(foreign_keys=[billed_by_staff_id])
