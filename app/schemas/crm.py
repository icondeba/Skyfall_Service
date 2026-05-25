from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.customer import CustomerRead
from app.schemas.order import OrderRead


class CRMCustomerRead(CustomerRead):
    tag: str


class CRMCustomerListRead(BaseModel):
    page: int
    limit: int
    total: int
    customers: list[CRMCustomerRead]


class CRMCustomerDetailRead(BaseModel):
    customer: CustomerRead
    tag: str
    orders: list[OrderRead]


class CRMExportRow(BaseModel):
    id: UUID
    phone: str
    name: str | None
    email: str | None
    tag: str
    visit_count: int
    total_spent: float
    last_visit: datetime | None

    model_config = ConfigDict(from_attributes=True)
