from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

PaymentMode = Literal["cash", "upi", "debit_card", "credit_card"]
PaymentStatus = Literal["pending", "success", "failed", "refunded"]


class RazorpayCreateOrderRequest(BaseModel):
    order_id: UUID
    amount_in_paise: int | None = Field(default=None, gt=0)
    amount: float | None = Field(default=None, gt=0)
    notes: dict[str, str] = Field(default_factory=dict)


class RazorpayCreateOrderResponse(BaseModel):
    razorpay_order_id: str
    amount: int
    currency: str = "INR"
    key_id: str | None
    qr_image_url: str
    payment_id: UUID | None = None
    status: PaymentStatus = "pending"
    gateway_response: dict = Field(default_factory=dict)


class RazorpayWebhookResponse(BaseModel):
    received: bool
    updated_payment_id: UUID | None = None
    event: str | None = None


class CashPaymentRequest(BaseModel):
    order_id: UUID
    amount_received: float | None = Field(default=None, gt=0)
    amount: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_amount(self) -> "CashPaymentRequest":
        if self.amount_received is None and self.amount is None:
            raise ValueError("amount_received is required")
        return self


class CardPaymentRequest(BaseModel):
    order_id: UUID
    mode: Literal["debit_card", "credit_card"]
    amount: float = Field(..., gt=0)


class PaymentRead(BaseModel):
    id: UUID
    order_id: UUID
    mode: PaymentMode
    amount: float
    status: PaymentStatus
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CashPaymentResponse(BaseModel):
    change_amount: float
    invoice_url: str | None = None
    payment: PaymentRead


class CardPaymentResponse(BaseModel):
    invoice_url: str | None = None
    payment: PaymentRead


class PaymentStatusRead(BaseModel):
    order_id: UUID
    mode: PaymentMode | None = None
    status: PaymentStatus | Literal["unpaid", "partial", "paid"]
    razorpay_payment_id: str | None = None
    paid_at: datetime | None = None
    amount: float
    total_amount: float
    paid_amount: float
    due_amount: float
    payments: list[PaymentRead]
