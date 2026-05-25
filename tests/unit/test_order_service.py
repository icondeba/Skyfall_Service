import asyncio
from types import SimpleNamespace
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock

from app.schemas.order import CreateOrderRequest, OrderItemCreate
from app.services.order_service import OrderService


def test_create_order_uses_repositories_without_real_database(test_tenant_id: UUID) -> None:
    db = MagicMock()
    table = SimpleNamespace(id=uuid4(), status="free")
    menu_item = SimpleNamespace(
        id=uuid4(),
        name="Skyfall Cappuccino",
        is_available=True,
        base_price=149.0,
        variants=[],
        addons=[],
    )
    order = SimpleNamespace(
        id=uuid4(),
        table_id=table.id,
        customer_id=None,
        status="pending",
        order_type="dine_in",
        subtotal=0.0,
        tax_amount=0.0,
        discount_amount=0.0,
        total_amount=0.0,
        special_instructions=None,
        items=[],
    )
    order_item = SimpleNamespace(unit_price=149.0, quantity=2, item_status="pending")

    order_repo = MagicMock()
    order_repo.create.return_value = order
    order_repo.create_order_item.side_effect = lambda _db, target_order, _data: target_order.items.append(order_item) or order_item
    order_repo.get_with_items.return_value = order

    table_repo = MagicMock()
    table_repo.get_by_id.return_value = table

    menu_repo = MagicMock()
    menu_repo.get_item_with_details.return_value = menu_item

    customer_repo = MagicMock()
    kot_service = SimpleNamespace(generate_for_order=AsyncMock(return_value=SimpleNamespace(id=uuid4(), kot_number=1)))

    service = OrderService(order_repo, table_repo, menu_repo, customer_repo, kot_service)
    payload = CreateOrderRequest(
        table_id=table.id,
        items=[OrderItemCreate(menu_item_id=menu_item.id, quantity=2)],
    )

    created = asyncio.run(service.create_order(db, test_tenant_id, payload))

    assert created.total_amount == 312.9
    table_repo.update_status.assert_called_once_with(db, test_tenant_id, table.id, "occupied")
    kot_service.generate_for_order.assert_awaited_once()
    db.commit.assert_called_once()
