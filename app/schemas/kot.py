from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

KOTStatus = Literal["new", "acknowledged", "completed"]


class KOTItemRead(BaseModel):
    order_item_id: UUID
    menu_item_id: UUID
    name: str
    quantity: int
    variant_name: str | None = None
    addons: list[dict] = Field(default_factory=list)
    special_instructions: str | None = None


class KOTRead(BaseModel):
    id: UUID
    order_id: UUID
    kot_number: int
    items_json: list[dict]
    status: KOTStatus
    order_special_instructions: str | None = None
    printed_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KOTListRead(BaseModel):
    kots: list[KOTRead]
