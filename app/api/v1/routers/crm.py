from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.dependencies import CurrentUser, check_plan, get_current_staff, get_db, get_tenant
from app.schemas.crm import CRMCustomerDetailRead, CRMCustomerListRead
from app.services.crm_service import CustomerTag, crm_service

router = APIRouter(prefix="/crm", tags=["crm"])


@router.get("/customers", response_model=CRMCustomerListRead)
async def list_crm_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    tag: CustomerTag | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
    _plan: None = Depends(check_plan("pro")),
) -> CRMCustomerListRead:
    return await crm_service.list_customers(db, tenant_id, page, limit, tag, search)


@router.get("/customers/{customer_id}", response_model=CRMCustomerDetailRead)
async def get_crm_customer(
    customer_id: UUID,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
    _plan: None = Depends(check_plan("pro")),
) -> CRMCustomerDetailRead:
    return await crm_service.get_customer_detail(db, tenant_id, customer_id)


@router.get("/export")
async def export_crm_customers(
    tag: CustomerTag | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
    _plan: None = Depends(check_plan("pro")),
) -> StreamingResponse:
    csv_text = await crm_service.export_customers(db, tenant_id, tag, search)
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=skyfall-customers.csv"},
    )
