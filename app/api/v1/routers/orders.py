from datetime import date as DateType
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import CurrentUser, get_current_staff, get_db, get_tenant
from app.schemas.order import CreateOrderRequest, OrderItemCreate, OrderListRead, OrderRead, OrderResponse, UpdateStatusRequest
from app.schemas.common import PaginatedResponse
from app.services.order_service import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: CreateOrderRequest,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    staff: CurrentUser = Depends(get_current_staff),
) -> OrderResponse:
    order = await order_service.create_order(db, tenant_id, payload, placed_by_staff_id=staff.id)
    return OrderResponse.model_validate(order)


@router.get("/active", response_model=OrderListRead)
async def get_active_orders(
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> OrderListRead:
    orders = await order_service.get_active_orders(db, tenant_id)
    return OrderListRead(orders=orders)


@router.get("/table/{table_id}/active", response_model=OrderListRead)
async def get_active_orders_for_table(
    table_id: str,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> OrderListRead:
    orders = await order_service.get_active_by_table(db, tenant_id, table_id)
    return OrderListRead(orders=orders)


@router.get("/history", response_model=PaginatedResponse[OrderRead])
async def get_order_history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=30, ge=1, le=100),
    date: DateType | None = Query(default=None),
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> dict:
    result = await order_service.get_history(db, tenant_id, page, limit, date)
    return {
        "items": [OrderRead.model_validate(o) for o in result.items],
        "total": result.total,
        "page": result.page,
        "limit": result.limit,
        "has_next": result.has_next,
    }


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
) -> OrderResponse:
    order = await order_service.get_order_detail(db, tenant_id, order_id)
    return OrderResponse.model_validate(order)


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    payload: UpdateStatusRequest,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> OrderResponse:
    order = await order_service.update_status(db, tenant_id, order_id, payload.status)
    return OrderResponse.model_validate(order)


@router.post("/{order_id}/items", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def add_order_items(
    order_id: UUID,
    payload: list[OrderItemCreate],
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> OrderResponse:
    order = await order_service.add_items(db, tenant_id, order_id, payload)
    return OrderResponse.model_validate(order)
