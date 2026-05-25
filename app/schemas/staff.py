from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

StaffRole = Literal["admin", "waiter", "kitchen"]


class StaffRead(BaseModel):
    id: UUID
    name: str
    email: str
    role: StaffRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StaffListRead(BaseModel):
    staff: list[StaffRead]


class StaffCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., min_length=3, max_length=255)
    role: StaffRole


class StaffUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    role: StaffRole | None = None
    is_active: bool | None = None
