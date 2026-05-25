from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import KOT, Order, OrderItem
from app.repositories.base_repository import BaseRepository


class KOTRepository(BaseRepository[KOT]):
    def __init__(self) -> None:
        super().__init__(KOT)

    def next_number(self, db: Session, tenant_id: UUID) -> int:
        statement = select(func.max(KOT.kot_number))
        if hasattr(KOT, "tenant_id"):
            statement = statement.where(KOT.tenant_id == tenant_id)
        return int(db.scalar(statement) or 0) + 1

    def get_with_order(self, db: Session, tenant_id: UUID, kot_id: UUID) -> KOT | None:
        statement = (
            select(KOT)
            .where(KOT.id == kot_id)
            .options(
                selectinload(KOT.order).selectinload(Order.items).selectinload(OrderItem.menu_item),
                selectinload(KOT.order).selectinload(Order.items).selectinload(OrderItem.variant),
            )
        )
        if hasattr(KOT, "tenant_id"):
            statement = statement.where(KOT.tenant_id == tenant_id)
        return db.scalar(statement)

    def get_active(self, db: Session, tenant_id: UUID) -> list[KOT]:
        statement = (
            select(KOT)
            .where(KOT.status != "completed")
            .options(
                selectinload(KOT.order).selectinload(Order.table),
                selectinload(KOT.order).selectinload(Order.items).selectinload(OrderItem.menu_item),
                selectinload(KOT.order).selectinload(Order.items).selectinload(OrderItem.variant),
            )
            .order_by(KOT.created_at.asc())
        )
        if hasattr(KOT, "tenant_id"):
            statement = statement.where(KOT.tenant_id == tenant_id)
        return list(db.scalars(statement))


kot_repository = KOTRepository()
