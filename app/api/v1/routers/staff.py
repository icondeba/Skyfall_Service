from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentUser, get_current_admin, get_db, get_tenant
from app.schemas.staff import StaffCreate, StaffListRead, StaffRead, StaffUpdate
from app.services.staff_service import staff_service

router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("", response_model=StaffListRead)
async def list_staff(
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _admin: CurrentUser = Depends(get_current_admin),
) -> StaffListRead:
    return StaffListRead(staff=await staff_service.list_staff(db, tenant_id))


@router.post("", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
async def create_staff(
    payload: StaffCreate,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _admin: CurrentUser = Depends(get_current_admin),
) -> StaffRead:
    staff = await staff_service.create_staff(db, tenant_id, payload)
    return StaffRead.model_validate(staff)


@router.patch("/{staff_id}", response_model=StaffRead)
async def update_staff(
    staff_id: UUID,
    payload: StaffUpdate,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _admin: CurrentUser = Depends(get_current_admin),
) -> StaffRead:
    staff = await staff_service.update_staff(db, tenant_id, staff_id, payload)
    return StaffRead.model_validate(staff)


@router.patch("/{staff_id}/activate", response_model=StaffRead)
async def activate_staff(
    staff_id: UUID,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _admin: CurrentUser = Depends(get_current_admin),
) -> StaffRead:
    staff = await staff_service.set_active(db, tenant_id, staff_id, True)
    return StaffRead.model_validate(staff)


@router.patch("/{staff_id}/deactivate", response_model=StaffRead)
async def deactivate_staff(
    staff_id: UUID,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _admin: CurrentUser = Depends(get_current_admin),
) -> StaffRead:
    staff = await staff_service.set_active(db, tenant_id, staff_id, False)
    return StaffRead.model_validate(staff)
