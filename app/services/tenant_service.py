from uuid import UUID
from typing import Any

from app.core.exceptions import PlanLimitExceededError, TenantNotFoundError
from app.models import Tenant
from app.repositories.tenant_repository import tenant_repository
from app.schemas.tenant import TenantCreateRequest, TenantUpdateRequest

PLAN_ORDER = {"starter": 1, "pro": 2, "enterprise": 3}


class TenantService:
    async def get_tenant(self, db: Any, tenant_id: UUID) -> Tenant:
        tenant = tenant_repository.get_by_id_unscoped(db, tenant_id)
        if tenant is None or not tenant.is_active:
            raise TenantNotFoundError("Tenant not found")
        return tenant

    async def create_tenant(self, db: Any, payload: TenantCreateRequest) -> Tenant:
        tenant = tenant_repository.create(db, UUID("00000000-0000-0000-0000-000000000000"), payload.model_dump())
        db.commit()
        db.refresh(tenant)
        return tenant

    async def update_tenant(self, db: Any, tenant_id: UUID, payload: TenantUpdateRequest) -> Tenant:
        tenant = tenant_repository.get_by_id_unscoped(db, tenant_id)
        if tenant is None:
            raise TenantNotFoundError("Tenant not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(tenant, field, value)
        db.commit()
        db.refresh(tenant)
        return tenant

    async def check_plan(self, db: Any, tenant_id: UUID, required_plan: str) -> None:
        tenant = await self.get_tenant(db, tenant_id)
        if PLAN_ORDER.get(tenant.plan, 0) < PLAN_ORDER.get(required_plan, 0):
            raise PlanLimitExceededError(f"{required_plan.title()} plan required")


tenant_service = TenantService()
