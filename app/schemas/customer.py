from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CustomerIdentifyRequest(BaseModel):
    phone: str = Field(..., min_length=6, max_length=32)
    name: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    birthday: date | None = None
    anniversary: date | None = None
    special_event_date: date | None = None
    special_event_name: str | None = Field(default=None, max_length=120)


class CustomerRead(BaseModel):
    id: UUID
    phone: str
    name: str | None = None
    email: str | None = None
    birthday: date | None = None
    anniversary: date | None = None
    special_event_date: date | None = None
    special_event_name: str | None = None
    visit_count: int
    total_spent: float
    last_visit: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerIdentifyResponse(BaseModel):
    customer: CustomerRead
    is_new: bool


class CustomerListRead(BaseModel):
    customers: list[CustomerRead]
