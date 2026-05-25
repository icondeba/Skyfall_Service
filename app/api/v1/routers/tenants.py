from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentUser, get_current_admin, get_current_user, get_db, get_tenant
from app.schemas.tenant import TenantCreateRequest, TenantResponse, TenantUpdateRequest
from app.services.tenant_service import tenant_service

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/current", response_model=TenantResponse)
async def get_current_tenant(
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _user: CurrentUser = Depends(get_current_user),
) -> TenantResponse:
    tenant = await tenant_service.get_tenant(db, tenant_id)
    return TenantResponse.model_validate(tenant)


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreateRequest,
    db: Any = Depends(get_db),
    _admin: CurrentUser = Depends(get_current_admin),
) -> TenantResponse:
    tenant = await tenant_service.create_tenant(db, payload)
    return TenantResponse.model_validate(tenant)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdateRequest,
    db: Any = Depends(get_db),
    _admin: CurrentUser = Depends(get_current_admin),
) -> TenantResponse:
    tenant = await tenant_service.update_tenant(db, tenant_id, payload)
    return TenantResponse.model_validate(tenant)
