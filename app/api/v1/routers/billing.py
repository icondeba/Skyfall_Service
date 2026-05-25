from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentUser, get_current_staff, get_db, get_tenant
from app.schemas.billing import BillingFinaliseRead, BillingRead
from app.services.billing_service import billing_service

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/finalise/{order_id}", response_model=BillingFinaliseRead)
async def finalise_bill(
    order_id: UUID,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    staff: CurrentUser = Depends(get_current_staff),
) -> BillingFinaliseRead:
    return await billing_service.finalise(db, tenant_id, order_id, billed_by_staff_id=staff.id)


@router.get("/{order_id}", response_model=BillingRead)
async def get_bill(
    order_id: UUID,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> BillingRead:
    return await billing_service.get_bill(db, tenant_id, order_id)
