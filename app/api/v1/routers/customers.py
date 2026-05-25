from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentUser, get_current_staff, get_db, get_tenant
from app.schemas.customer import CustomerIdentifyRequest, CustomerIdentifyResponse, CustomerListRead, CustomerRead
from app.services.customer_service import customer_service

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("/identify", response_model=CustomerIdentifyResponse, status_code=status.HTTP_200_OK)
async def identify_customer(
    payload: CustomerIdentifyRequest,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
) -> CustomerIdentifyResponse:
    return await customer_service.identify(db, tenant_id, payload)


@router.get("/repeat", response_model=CustomerListRead)
async def get_repeat_customers(
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> CustomerListRead:
    return await customer_service.get_repeat_customers(db, tenant_id)


@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: UUID,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> CustomerRead:
    customer = await customer_service.get_customer(db, tenant_id, customer_id)
    return CustomerRead.model_validate(customer)
