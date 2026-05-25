from uuid import UUID
from typing import Any

from app.core.config import settings
from app.core.exceptions import (
    DomainError,
    MenuItemUnavailableError,
    OrderNotFoundError,
    TableOccupiedError,
)
from app.models import Order
from app.repositories.customer_repository import customer_repository
from app.repositories.menu_repository import menu_repository
from app.repositories.order_repository import ACTIVE_ORDER_STATUSES, order_repository
from app.repositories.table_repository import table_repository
from app.schemas.order import CreateOrderRequest, OrderItemCreate
from app.services.kot_service import kot_service
from app.services.integrations.supabase_realtime import publish_realtime

LEGAL_STATUS_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"preparing", "cancelled"},
    "preparing": {"ready", "cancelled"},
    "ready": {"served", "cancelled"},
    "served": set(),
    "cancelled": set(),
}


class OrderService:
    def __init__(
        self,
        order_repo=order_repository,
        table_repo=table_repository,
        menu_repo=menu_repository,
        customer_repo=customer_repository,
        kot_svc=kot_service,
    ) -> None:
        self.order_repo = order_repo
        self.table_repo = table_repo
        self.menu_repo = menu_repo
        self.customer_repo = customer_repo
        self.kot_service = kot_svc

    def _build_order_item_data(self, db: Any, tenant_id: UUID, requested_item: OrderItemCreate) -> dict:
        menu_item = self.menu_repo.get_item_with_details(db, tenant_id, requested_item.menu_item_id)
        if menu_item is None:
            raise DomainError(
                f"Menu item {requested_item.menu_item_id} not found",
                status_code=404,
                error_code="menu_item_not_found",
            )
        if not menu_item.is_available:
            raise MenuItemUnavailableError(f"{menu_item.name} is not available")

        variant = None
        if requested_item.variant_id is not None:
            variant = next(
                (candidate for candidate in menu_item.variants if candidate.id == requested_item.variant_id),
                None,
            )
            if variant is None:
                raise DomainError(
                    f"Variant {requested_item.variant_id} does not belong to {menu_item.name}",
                    status_code=400,
                    error_code="invalid_item_variant",
                )

        addon_payloads: list[dict] = []
        addons_by_id = {addon.id: addon for addon in menu_item.addons}
        for addon_id in requested_item.addon_ids:
            addon = addons_by_id.get(addon_id)
            if addon is None:
                raise DomainError(
                    f"Addon {addon_id} does not belong to {menu_item.name}",
                    status_code=400,
                    error_code="invalid_item_addon",
                )
            if not addon.is_available:
                raise MenuItemUnavailableError(f"Addon {addon.name} is not available")
            addon_payloads.append(
                {
                    "id": str(addon.id),
                    "name": addon.name,
                    "extra_price": addon.extra_price,
                }
            )

        unit_price = menu_item.base_price
        if variant is not None:
            unit_price += variant.price_modifier
        unit_price += sum(addon["extra_price"] for addon in addon_payloads)
        return {
            "menu_item": menu_item,
            "variant": variant,
            "quantity": requested_item.quantity,
            "unit_price": round(unit_price, 2),
            "addons_json": addon_payloads,
            "special_instructions": requested_item.special_instructions,
        }

    def _recalculate_totals(self, order: Order) -> None:
        subtotal = sum(item.unit_price * item.quantity for item in order.items)
        taxable_amount = max(subtotal - order.discount_amount, 0.0)
        order.subtotal = round(subtotal, 2)
        order.tax_amount = round(taxable_amount * settings.TAX_RATE, 2)
        order.total_amount = round(taxable_amount + order.tax_amount, 2)

    def _release_table_if_order_closed(self, db: Any, tenant_id: UUID, table_id: UUID | None) -> None:
        if table_id is None:
            return
        if self.order_repo.count_open_for_table(db, tenant_id, table_id):
            return
        self.table_repo.update_status(db, tenant_id, table_id, "free")

    async def create_order(self, db: Any, tenant_id: UUID, payload: CreateOrderRequest, placed_by_staff_id: UUID | None = None) -> Order:
        if payload.customer_id is not None and self.customer_repo.get_by_id(db, tenant_id, payload.customer_id) is None:
            raise DomainError("Customer not found", status_code=404, error_code="customer_not_found")

        table = None
        if payload.order_type != "takeaway":
            if payload.table_id is None:
                raise DomainError("table_id is required for dine-in orders", status_code=400, error_code="table_required")
            table = self.table_repo.resolve_table_reference(db, tenant_id, payload.table_id)
            if table is None:
                raise DomainError("Table not found", status_code=404, error_code="table_not_found")
            open_orders_count = self.order_repo.count_open_for_table(db, tenant_id, table.id)
            if table.status in {"occupied", "bill_requested"} and open_orders_count == 0:
                table.status = "free"
                db.flush()
            elif open_orders_count > 0:
                raise TableOccupiedError("Table already has an open order")
            elif table.status == "reserved":
                raise DomainError("Table is reserved", status_code=409, error_code="table_reserved")

        order = self.order_repo.create(
            db,
            tenant_id,
            {
                "table_id": table.id if table else None,
                "customer_id": payload.customer_id,
                "placed_by_staff_id": placed_by_staff_id,
                "status": "pending",
                "order_type": payload.order_type,
                "subtotal": 0.0,
                "tax_amount": 0.0,
                "discount_amount": payload.discount_amount,
                "total_amount": 0.0,
                "special_instructions": payload.special_instructions,
            },
        )
        order_items = [
            self.order_repo.create_order_item(
                db,
                order,
                self._build_order_item_data(db, tenant_id, requested_item),
            )
            for requested_item in payload.items
        ]
        self._recalculate_totals(order)
        if table is not None:
            self.table_repo.update_status(db, tenant_id, table.id, "occupied")

        kot = await self.kot_service.generate_for_order(db, tenant_id, order, order_items, commit=False)
        db.commit()
        created_order = self.order_repo.get_with_items(db, tenant_id, order.id) or order
        publish_realtime(
            "order.created",
            {"order_id": created_order.id, "kot_id": kot.id, "status": created_order.status},
            settings,
        )
        publish_realtime(
            "kot.created",
            {"kot_id": kot.id, "order_id": created_order.id, "kot_number": kot.kot_number},
            settings,
        )
        return created_order

    async def add_items(self, db: Any, tenant_id: UUID, order_id: UUID, items: list[OrderItemCreate]) -> Order:
        if not items:
            raise DomainError("At least one order item is required", status_code=422, error_code="empty_order_items")
        order = self.order_repo.get_with_items(db, tenant_id, order_id)
        if order is None:
            raise OrderNotFoundError("Order not found")
        if order.status in {"served", "cancelled"}:
            raise DomainError("Cannot add items to a closed order", status_code=409, error_code="order_closed")

        new_items = [
            self.order_repo.create_order_item(
                db,
                order,
                self._build_order_item_data(db, tenant_id, requested_item),
            )
            for requested_item in items
        ]
        self._recalculate_totals(order)
        kot = await self.kot_service.generate_for_order(db, tenant_id, order, new_items, commit=False)
        db.commit()
        updated_order = self.order_repo.get_with_items(db, tenant_id, order.id) or order
        publish_realtime(
            "order.items_added",
            {"order_id": updated_order.id, "kot_id": kot.id, "status": updated_order.status},
            settings,
        )
        publish_realtime(
            "kot.created",
            {"kot_id": kot.id, "order_id": updated_order.id, "kot_number": kot.kot_number},
            settings,
        )
        return updated_order

    async def update_status(self, db: Any, tenant_id: UUID, order_id: UUID, status: str) -> Order:
        order = self.order_repo.get_with_items(db, tenant_id, order_id)
        if order is None:
            raise OrderNotFoundError("Order not found")
        if status != "cancelled" and status != order.status:
            allowed = LEGAL_STATUS_TRANSITIONS.get(order.status, set())
            if status not in allowed:
                raise DomainError(
                    f"Illegal status transition: {order.status} -> {status}",
                    status_code=409,
                    error_code="illegal_order_status_transition",
                )
        order.status = status
        if status in {"served", "cancelled"}:
            self._release_table_if_order_closed(db, tenant_id, order.table_id)
        db.commit()
        updated_order = self.order_repo.get_with_items(db, tenant_id, order_id) or order
        publish_realtime(
            "order.status_updated",
            {"order_id": updated_order.id, "status": updated_order.status},
            settings,
        )
        return updated_order

    async def get_active_orders(self, db: Any, tenant_id: UUID) -> list[Order]:
        return self.order_repo.get_active_orders(db, tenant_id)

    async def get_order_detail(self, db: Any, tenant_id: UUID, order_id: UUID) -> Order:
        order = self.order_repo.get_with_items(db, tenant_id, order_id)
        if order is None:
            raise OrderNotFoundError("Order not found")
        return order

    async def get_active_by_table(self, db: Any, tenant_id: UUID, table_id: UUID | int | str) -> list[Order]:
        table = self.table_repo.resolve_table_reference(db, tenant_id, table_id)
        if table is None:
            raise DomainError("Table not found", status_code=404, error_code="table_not_found")
        return self.order_repo.get_active_by_table(db, tenant_id, table.id)

    async def get_history(self, db: Any, tenant_id: UUID, page: int, limit: int, order_date: "date | None" = None):
        from datetime import date
        return self.order_repo.get_served_paginated(db, tenant_id, page, limit, order_date)

    async def cancel_order(self, db: Any, tenant_id: UUID, order_id: UUID, reason: str | None = None) -> Order:
        order = self.order_repo.get_with_items(db, tenant_id, order_id)
        if order is None:
            raise OrderNotFoundError("Order not found")
        order.status = "cancelled"
        if reason:
            order.special_instructions = f"{order.special_instructions or ''}\nCancelled: {reason}".strip()
        self._release_table_if_order_closed(db, tenant_id, order.table_id)
        db.commit()
        return self.order_repo.get_with_items(db, tenant_id, order_id) or order


order_service = OrderService()
