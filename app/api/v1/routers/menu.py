from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentUser, get_current_admin, get_db, get_tenant
from app.schemas.menu import CategoryRead, MenuItemAvailabilityUpdate, MenuItemCreate, MenuItemRead, MenuItemUpdate, MenuRead
from app.services.menu_service import menu_service

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=MenuRead)
async def list_menu(db: Any = Depends(get_db), tenant_id: UUID = Depends(get_tenant)) -> MenuRead:
    return await menu_service.list_menu(db, tenant_id)


@router.get("/items/{item_id}", response_model=MenuItemRead)
async def get_menu_item(
    item_id: UUID,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
) -> MenuItemRead:
    item = await menu_service.get_item(db, tenant_id, item_id)
    return MenuItemRead.model_validate(item)


@router.get("/categories", response_model=list[CategoryRead])
async def list_categories(db: Any = Depends(get_db), tenant_id: UUID = Depends(get_tenant)) -> list[CategoryRead]:
    categories = await menu_service.list_categories(db, tenant_id)
    return [CategoryRead.model_validate(category) for category in categories]


@router.post("/items", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    payload: MenuItemCreate,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _admin: CurrentUser = Depends(get_current_admin),
) -> MenuItemRead:
    item = await menu_service.create_item(db, tenant_id, payload)
    return MenuItemRead.model_validate(item)


@router.patch("/items/{item_id}", response_model=MenuItemRead)
async def update_menu_item(
    item_id: UUID,
    payload: MenuItemUpdate,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _admin: CurrentUser = Depends(get_current_admin),
) -> MenuItemRead:
    item = await menu_service.update_item(db, tenant_id, item_id, payload)
    return MenuItemRead.model_validate(item)


@router.patch("/items/{item_id}/availability", response_model=MenuItemRead)
async def update_menu_item_availability(
    item_id: UUID,
    payload: MenuItemAvailabilityUpdate,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _admin: CurrentUser = Depends(get_current_admin),
) -> MenuItemRead:
    item = await menu_service.update_availability(db, tenant_id, item_id, payload.is_available)
    return MenuItemRead.model_validate(item)
