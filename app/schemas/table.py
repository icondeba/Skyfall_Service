from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TableStatus = Literal["free", "occupied", "reserved", "bill_requested"]


class TableStatusUpdate(BaseModel):
    status: TableStatus


class TableCreate(BaseModel):
    table_number: int = Field(gt=0)
    capacity: int = Field(default=4, gt=0)


class TableUpdate(BaseModel):
    table_number: int | None = Field(default=None, gt=0)
    capacity: int | None = Field(default=None, gt=0)


class TableRead(BaseModel):
    id: UUID
    table_number: int
    qr_code_url: str | None = None
    status: TableStatus
    capacity: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TableListRead(BaseModel):
    tables: list[TableRead]
