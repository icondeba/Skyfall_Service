from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ItemVariantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    price_modifier: float = 0.0


class ItemVariantCreate(ItemVariantBase):
    pass


class ItemVariantRead(ItemVariantBase):
    id: UUID
    item_id: UUID

    model_config = ConfigDict(from_attributes=True)


class ItemAddonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    extra_price: float = Field(..., ge=0)
    is_available: bool = True


class ItemAddonCreate(ItemAddonBase):
    pass


class ItemAddonRead(ItemAddonBase):
    id: UUID
    item_id: UUID

    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    icon: str = Field(..., min_length=1, max_length=16)
    display_order: int = 0
    is_active: bool = True


class CategoryRead(CategoryBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MenuItemBase(BaseModel):
    category_id: UUID
    name: str = Field(..., min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    base_price: float = Field(..., ge=0)
    image_url: str | None = Field(default=None, max_length=1024)
    is_available: bool = True
    is_veg: bool = True
    prep_time_minutes: int = Field(default=10, ge=1)


class MenuItemCreate(MenuItemBase):
    variants: list[ItemVariantCreate] = Field(default_factory=list)
    addons: list[ItemAddonCreate] = Field(default_factory=list)


class MenuItemUpdate(BaseModel):
    category_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    base_price: float | None = Field(default=None, ge=0)
    image_url: str | None = Field(default=None, max_length=1024)
    is_available: bool | None = None
    is_veg: bool | None = None
    prep_time_minutes: int | None = Field(default=None, ge=1)
    variants: list[ItemVariantCreate] | None = None
    addons: list[ItemAddonCreate] | None = None


class MenuItemAvailabilityUpdate(BaseModel):
    is_available: bool


class MenuItemRead(MenuItemBase):
    id: UUID
    created_at: datetime
    category: CategoryRead | None = None
    variants: list[ItemVariantRead] = Field(default_factory=list)
    addons: list[ItemAddonRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CategoryWithItems(CategoryRead):
    menu_items: list[MenuItemRead] = Field(default_factory=list)


class MenuRead(BaseModel):
    categories: list[CategoryWithItems]
