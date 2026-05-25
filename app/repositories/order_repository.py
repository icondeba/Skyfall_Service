from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import MenuItem, Order, OrderItem, Payment
from app.repositories.base_repository import BaseRepository
from app.schemas.common import PaginatedResponse

ACTIVE_ORDER_STATUSES = ("pending", "confirmed", "preparing", "ready")


class OrderRepository(BaseRepository[Order]):
    def __init__(self) -> None:
        super().__init__(Order)

    def _with_details(self) -> tuple[Any, ...]:
        from app.models.invoice import Invoice
        from app.models.staff import Staff
        return (
            selectinload(Order.items).selectinload(OrderItem.menu_item),
            selectinload(Order.items).selectinload(OrderItem.variant),
            selectinload(Order.kots),
            selectinload(Order.payments),
            selectinload(Order.invoice).selectinload(Invoice.billed_by_staff),
            selectinload(Order.customer),
            selectinload(Order.table),
            selectinload(Order.placed_by_staff),
        )

    def create_order_item(self, db: Session, order: Order, item_data: dict) -> OrderItem:
        order_item = OrderItem(order=order, **item_data)
        db.add(order_item)
        db.flush()
        return order_item

    def get_active_orders(self, db: Session, tenant_id: UUID) -> list[Order]:
        paid_subquery = (
            select(
                Payment.order_id.label("order_id"),
                func.coalesce(func.sum(Payment.amount), 0.0).label("paid_amount"),
            )
            .where(Payment.status == "success")
            .group_by(Payment.order_id)
            .subquery()
        )
        statement = (
            select(Order)
            .outerjoin(paid_subquery, paid_subquery.c.order_id == Order.id)
            .where(
                or_(
                    Order.status.in_(ACTIVE_ORDER_STATUSES),
                    and_(
                        Order.status == "served",
                        func.coalesce(paid_subquery.c.paid_amount, 0.0) + 0.01 < Order.total_amount,
                    ),
                )
            )
            .options(*self._with_details())
            .order_by(Order.created_at.desc())
        )
        if hasattr(Order, "tenant_id"):
            statement = statement.where(Order.tenant_id == tenant_id)
        return list(db.scalars(statement))

    def get_by_table(self, db: Session, tenant_id: UUID, table_id: UUID) -> Order | None:
        statement = (
            select(Order)
            .where(Order.table_id == table_id, Order.status.in_(ACTIVE_ORDER_STATUSES))
            .options(*self._with_details())
            .order_by(Order.created_at.desc())
        )
        if hasattr(Order, "tenant_id"):
            statement = statement.where(Order.tenant_id == tenant_id)
        return db.scalars(statement).first()

    def get_active_by_table(self, db: Session, tenant_id: UUID, table_id: UUID) -> list[Order]:
        statement = (
            select(Order)
            .where(Order.table_id == table_id, Order.status.in_(ACTIVE_ORDER_STATUSES))
            .options(*self._with_details())
            .order_by(Order.created_at.desc())
        )
        if hasattr(Order, "tenant_id"):
            statement = statement.where(Order.tenant_id == tenant_id)
        return list(db.scalars(statement))

    def get_by_customer(self, db: Session, tenant_id: UUID, customer_id: UUID) -> list[Order]:
        statement = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .options(*self._with_details())
            .order_by(Order.created_at.desc())
        )
        if hasattr(Order, "tenant_id"):
            statement = statement.where(Order.tenant_id == tenant_id)
        return list(db.scalars(statement))

    def get_with_items(self, db: Session, tenant_id: UUID, order_id: UUID) -> Order | None:
        statement = select(Order).where(Order.id == order_id).options(*self._with_details())
        if hasattr(Order, "tenant_id"):
            statement = statement.where(Order.tenant_id == tenant_id)
        return db.scalar(statement)

    def get_daily_orders(self, db: Session, tenant_id: UUID, order_date: date) -> list[Order]:
        start = datetime.combine(order_date, time.min)
        end = datetime.combine(order_date, time.max)
        statement = (
            select(Order)
            .where(Order.created_at >= start, Order.created_at <= end)
            .order_by(Order.created_at.desc())
        )
        if hasattr(Order, "tenant_id"):
            statement = statement.where(Order.tenant_id == tenant_id)
        return list(db.scalars(statement))

    def get_orders_paginated(
        self,
        db: Session,
        tenant_id: UUID,
        page: int,
        limit: int,
        status_filter: str | None = None,
    ) -> PaginatedResponse[Order]:
        statement = select(Order).order_by(Order.created_at.desc())
        count_statement = select(func.count(Order.id))
        if hasattr(Order, "tenant_id"):
            statement = statement.where(Order.tenant_id == tenant_id)
            count_statement = count_statement.where(Order.tenant_id == tenant_id)
        if status_filter:
            statement = statement.where(Order.status == status_filter)
            count_statement = count_statement.where(Order.status == status_filter)
        total = int(db.scalar(count_statement) or 0)
        items = list(db.scalars(statement.offset((page - 1) * limit).limit(limit)))
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            has_next=page * limit < total,
        )

    def update_status(self, db: Session, tenant_id: UUID, order_id: UUID, new_status: str) -> Order | None:
        order = self.get_by_id(db, tenant_id, order_id)
        if order is None:
            return None
        order.status = new_status
        db.flush()
        return order

    def count_active_for_table(self, db: Session, tenant_id: UUID, table_id: UUID) -> int:
        statement = select(func.count(Order.id)).where(
            Order.table_id == table_id,
            Order.status.in_(ACTIVE_ORDER_STATUSES),
        )
        if hasattr(Order, "tenant_id"):
            statement = statement.where(Order.tenant_id == tenant_id)
        return int(db.scalar(statement) or 0)

    def count_open_for_table(self, db: Session, tenant_id: UUID, table_id: UUID) -> int:
        paid_subquery = (
            select(
                Payment.order_id.label("order_id"),
                func.coalesce(func.sum(Payment.amount), 0.0).label("paid_amount"),
            )
            .where(Payment.status == "success")
            .group_by(Payment.order_id)
            .subquery()
        )
        statement = (
            select(func.count(Order.id))
            .outerjoin(paid_subquery, paid_subquery.c.order_id == Order.id)
            .where(
                Order.table_id == table_id,
                or_(
                    Order.status.in_(ACTIVE_ORDER_STATUSES),
                    and_(
                        Order.status == "served",
                        func.coalesce(paid_subquery.c.paid_amount, 0.0) + 0.01 < Order.total_amount,
                    ),
                ),
            )
        )
        if hasattr(Order, "tenant_id"):
            statement = statement.where(Order.tenant_id == tenant_id)
        return int(db.scalar(statement) or 0)

    def get_served_paginated(
        self,
        db: Session,
        tenant_id: UUID,
        page: int,
        limit: int,
        order_date: date | None = None,
    ) -> "PaginatedResponse[Order]":
        from app.schemas.common import PaginatedResponse
        target_date = order_date or date.today()
        start = datetime.combine(target_date, time.min)
        end = datetime.combine(target_date, time.max)
        base_filter = [Order.status == "served", Order.created_at >= start, Order.created_at <= end]
        if hasattr(Order, "tenant_id"):
            base_filter.append(Order.tenant_id == tenant_id)
        total = int(db.scalar(select(func.count(Order.id)).where(*base_filter)) or 0)
        items = list(
            db.scalars(
                select(Order)
                .where(*base_filter)
                .options(*self._with_details())
                .order_by(Order.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
        )
        return PaginatedResponse(items=items, total=total, page=page, limit=limit, has_next=page * limit < total)

    def summary_between(self, db: Session, tenant_id: UUID, start: datetime, end: datetime) -> tuple[int, float]:
        statement = select(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total_amount), 0.0),
        ).where(
            Order.created_at >= start,
            Order.created_at <= end,
            Order.status != "cancelled",
        )
        if hasattr(Order, "tenant_id"):
            statement = statement.where(Order.tenant_id == tenant_id)
        count, total = db.execute(statement).one()
        return int(count or 0), float(total or 0.0)

    def count_active(self, db: Session, tenant_id: UUID) -> int:
        statement = select(func.count(Order.id)).where(Order.status.in_(ACTIVE_ORDER_STATUSES))
        if hasattr(Order, "tenant_id"):
            statement = statement.where(Order.tenant_id == tenant_id)
        return int(db.scalar(statement) or 0)

    def get_between(self, db: Session, tenant_id: UUID, start: datetime, end: datetime) -> list[Order]:
        statement = select(Order).where(
            Order.created_at >= start,
            Order.created_at <= end,
            Order.status != "cancelled",
        )
        if hasattr(Order, "tenant_id"):
            statement = statement.where(Order.tenant_id == tenant_id)
        return list(db.scalars(statement))

    def top_items(self, db: Session, tenant_id: UUID, limit: int) -> list[tuple]:
        statement = (
            select(
                MenuItem.id,
                MenuItem.name,
                func.coalesce(func.sum(OrderItem.quantity), 0),
                func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0.0),
            )
            .join(OrderItem, OrderItem.menu_item_id == MenuItem.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.status != "cancelled")
            .group_by(MenuItem.id, MenuItem.name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(limit)
        )
        if hasattr(Order, "tenant_id"):
            statement = statement.where(Order.tenant_id == tenant_id)
        return list(db.execute(statement).all())


order_repository = OrderRepository()
