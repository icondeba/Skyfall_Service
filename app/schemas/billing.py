from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.order import OrderItemRead, OrderRead, StaffBrief
from app.schemas.payment import PaymentRead


class InvoiceRead(BaseModel):
    id: UUID
    order_id: UUID
    invoice_number: str
    pdf_url: str | None = None
    whatsapp_sent: bool
    sms_sent: bool
    created_at: datetime
    billed_by_staff: StaffBrief | None = None

    model_config = ConfigDict(from_attributes=True)


class BillingRead(BaseModel):
    order: OrderRead
    invoice: InvoiceRead | None = None
    items: list[OrderItemRead]
    payments: list[PaymentRead]
    subtotal: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    paid_amount: float
    due_amount: float
    payment_status: str


class BillingFinaliseRead(BaseModel):
    invoice_url: str
    order_id: UUID
    total_amount: float
    table_number: int | None = None
