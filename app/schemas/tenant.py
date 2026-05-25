from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseSchema

TenantPlan = Literal["starter", "pro", "enterprise"]


class TenantCreateRequest(BaseSchema):
    name: str = Field(..., min_length=1, max_length=160)
    slug: str = Field(..., min_length=1, max_length=120)
    plan: TenantPlan = "starter"


class TenantUpdateRequest(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    plan: TenantPlan | None = None
    is_active: bool | None = None


class TenantResponse(BaseSchema):
    id: UUID
    name: str
    slug: str
    plan: TenantPlan
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
