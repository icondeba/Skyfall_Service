from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentUser, get_current_staff, get_db, get_tenant
from app.schemas.kot import KOTListRead, KOTRead
from app.services.kot_service import kot_service

router = APIRouter(prefix="/kot", tags=["kot"])


@router.post("/generate/{order_id}", response_model=KOTRead, status_code=status.HTTP_201_CREATED)
async def generate_kot(
    order_id: UUID,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> KOTRead:
    kot = await kot_service.generate(db, tenant_id, order_id)
    return KOTRead.model_validate(kot)


@router.get("/active", response_model=KOTListRead)
async def get_active_kots(
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> KOTListRead:
    return KOTListRead(kots=await kot_service.get_active(db, tenant_id))


@router.patch("/{kot_id}/acknowledge", response_model=KOTRead)
async def acknowledge_kot(
    kot_id: UUID,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> KOTRead:
    kot = await kot_service.acknowledge(db, tenant_id, kot_id)
    return KOTRead.model_validate(kot)


@router.patch("/{kot_id}/complete", response_model=KOTRead)
async def complete_kot(
    kot_id: UUID,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> KOTRead:
    kot = await kot_service.complete(db, tenant_id, kot_id)
    return KOTRead.model_validate(kot)
