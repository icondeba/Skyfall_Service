from datetime import UTC, datetime
from typing import Any, Sequence
from uuid import UUID

from app.core.exceptions import DomainError
from app.models import KOT, Order, OrderItem
from app.repositories.kot_repository import kot_repository
from app.repositories.order_repository import order_repository
from app.services.integrations.supabase_realtime import publish_realtime
from app.core.config import settings


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def build_kot_items(order_items: Sequence[OrderItem]) -> list[dict]:
    return [
        {
            "order_item_id": str(order_item.id),
            "menu_item_id": str(order_item.menu_item_id),
            "name": order_item.menu_item.name if order_item.menu_item else "Menu item",
            "quantity": order_item.quantity,
            "variant_name": order_item.variant.name if order_item.variant else None,
            "addons": order_item.addons_json,
            "special_instructions": order_item.special_instructions,
        }
        for order_item in order_items
    ]


class KOTService:
    async def generate_for_order(
        self,
        db: Any,
        tenant_id: UUID,
        order: Order,
        order_items: Sequence[OrderItem] | None = None,
        commit: bool = True,
    ) -> KOT:
        selected_items = list(order_items if order_items is not None else order.items)
        if not selected_items:
            raise DomainError("Order has no items for KOT generation", status_code=400, error_code="empty_kot")
        kot = kot_repository.create(
            db,
            tenant_id,
            {
                "order": order,
                "kot_number": kot_repository.next_number(db, tenant_id),
                "items_json": build_kot_items(selected_items),
                "status": "new",
            },
        )
        for order_item in selected_items:
            order_item.item_status = "preparing"
        if order.status in {"pending", "confirmed"}:
            order.status = "preparing"
        if commit:
            db.commit()
            publish_realtime(
                "kot.created",
                {"kot_id": kot.id, "order_id": order.id, "kot_number": kot.kot_number},
                settings,
            )
        return kot

    async def generate(self, db: Any, tenant_id: UUID, order_id: UUID) -> KOT:
        order = order_repository.get_with_items(db, tenant_id, order_id)
        if order is None:
            raise DomainError("Order not found", status_code=404, error_code="order_not_found")
        if order.status in {"served", "cancelled"}:
            raise DomainError("Cannot generate KOT for a closed order", status_code=409, error_code="order_closed")
        kot = await self.generate_for_order(db, tenant_id, order, commit=True)
        return kot_repository.get_with_order(db, tenant_id, kot.id) or kot

    async def get_active(self, db: Any, tenant_id: UUID) -> list[KOT]:
        return kot_repository.get_active(db, tenant_id)

    async def acknowledge(self, db: Any, tenant_id: UUID, kot_id: UUID) -> KOT:
        kot = kot_repository.get_with_order(db, tenant_id, kot_id)
        if kot is None:
            raise DomainError("KOT not found", status_code=404, error_code="kot_not_found")
        if kot.status == "completed":
            raise DomainError("Completed KOT cannot be acknowledged", status_code=409, error_code="kot_completed")
        kot.status = "acknowledged"
        if kot.printed_at is None:
            kot.printed_at = utc_now()
        db.commit()
        publish_realtime("kot.acknowledged", {"kot_id": kot.id, "order_id": kot.order_id}, settings)
        return kot_repository.get_with_order(db, tenant_id, kot.id) or kot

    async def complete(self, db: Any, tenant_id: UUID, kot_id: UUID) -> KOT:
        kot = kot_repository.get_with_order(db, tenant_id, kot_id)
        if kot is None:
            raise DomainError("KOT not found", status_code=404, error_code="kot_not_found")
        if kot.status == "completed":
            return kot
        order_item_ids = {
            UUID(str(item["order_item_id"]))
            for item in kot.items_json
            if item.get("order_item_id")
        }
        for order_item in kot.order.items:
            if order_item.id in order_item_ids:
                order_item.item_status = "ready"
        kot.status = "completed"
        if kot.order.items and all(item.item_status == "ready" for item in kot.order.items):
            kot.order.status = "ready"
        db.commit()
        publish_realtime("kot.completed", {"kot_id": kot.id, "order_id": kot.order_id}, settings)
        return kot_repository.get_with_order(db, tenant_id, kot.id) or kot


kot_service = KOTService()
