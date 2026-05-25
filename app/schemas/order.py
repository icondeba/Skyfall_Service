from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

OrderStatus = Literal["pending", "confirmed", "preparing", "ready", "served", "cancelled"]
OrderType = Literal["dine_in", "takeaway"]
OrderItemStatus = Literal["pending", "preparing", "ready"]
TableReference = UUID | int | str


class OrderItemCreate(BaseModel):
    menu_item_id: UUID
    quantity: int = Field(..., ge=1)
    variant_id: UUID | None = None
    addon_ids: list[UUID] = Field(default_factory=list)
    special_instructions: str | None = Field(default=None, max_length=1000)


class OrderCreate(BaseModel):
    table_id: TableReference | None = None
    customer_id: UUID | None = None
    order_type: OrderType = "dine_in"
    discount_amount: float = Field(default=0.0, ge=0)
    special_instructions: str | None = Field(default=None, max_length=1000)
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class MenuItemBrief(BaseModel):
    id: UUID
    name: str
    base_price: float
    image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ItemVariantBrief(BaseModel):
    id: UUID
    name: str
    price_modifier: float

    model_config = ConfigDict(from_attributes=True)


class TableBrief(BaseModel):
    id: UUID
    table_number: int
    status: Literal["free", "occupied", "reserved", "bill_requested"]
    capacity: int

    model_config = ConfigDict(from_attributes=True)


class StaffBrief(BaseModel):
    id: UUID
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class OrderItemRead(BaseModel):
    id: UUID
    order_id: UUID
    menu_item_id: UUID
    variant_id: UUID | None = None
    quantity: int
    unit_price: float
    addons_json: list[dict]
    special_instructions: str | None = None
    item_status: OrderItemStatus
    menu_item: MenuItemBrief | None = None
    variant: ItemVariantBrief | None = None

    model_config = ConfigDict(from_attributes=True)


class KOTSummary(BaseModel):
    id: UUID
    kot_number: int
    items_json: list[dict] = Field(default_factory=list)
    status: Literal["new", "acknowledged", "completed"]
    printed_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentSummary(BaseModel):
    id: UUID
    mode: Literal["cash", "upi", "debit_card", "credit_card"]
    amount: float
    status: Literal["pending", "success", "failed", "refunded"]
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerBrief(BaseModel):
    id: UUID
    name: str | None = None
    phone: str
    email: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: UUID
    table_id: UUID | None = None
    customer_id: UUID | None = None
    status: OrderStatus
    order_type: OrderType
    subtotal: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    special_instructions: str | None = None
    created_at: datetime
    updated_at: datetime
    table: TableBrief | None = None
    customer: CustomerBrief | None = None
    placed_by_staff: StaffBrief | None = None
    items: list[OrderItemRead] = Field(default_factory=list)
    kots: list[KOTSummary] = Field(default_factory=list)
    payments: list[PaymentSummary] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class OrderListRead(BaseModel):
    orders: list[OrderRead]


CreateOrderRequest = OrderCreate
OrderResponse = OrderRead
UpdateStatusRequest = OrderStatusUpdate
AddOrderItemsRequest = list[OrderItemCreate]
