from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status

from app.api.dependencies import DEV_TENANT_ID, CurrentUser, get_current_staff, get_db, get_tenant
from app.schemas.payment import (
    CardPaymentRequest,
    CardPaymentResponse,
    CashPaymentRequest,
    CashPaymentResponse,
    PaymentStatusRead,
    RazorpayCreateOrderRequest,
    RazorpayCreateOrderResponse,
    RazorpayWebhookResponse,
)
from app.services.payment_service import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/razorpay/create-order", response_model=RazorpayCreateOrderResponse)
async def create_razorpay_order(
    payload: RazorpayCreateOrderRequest,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> RazorpayCreateOrderResponse:
    return await payment_service.create_razorpay_order(db, tenant_id, payload)


@router.post("/razorpay/webhook", response_model=RazorpayWebhookResponse)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None),
    db: Any = Depends(get_db),
) -> RazorpayWebhookResponse:
    return await payment_service.handle_razorpay_webhook(db, DEV_TENANT_ID, await request.body(), x_razorpay_signature)


@router.post("/cash", response_model=CashPaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_cash_payment(
    payload: CashPaymentRequest,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> CashPaymentResponse:
    return await payment_service.create_cash_payment(db, tenant_id, payload)


@router.post("/card", response_model=CardPaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_card_payment(
    payload: CardPaymentRequest,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> CardPaymentResponse:
    return await payment_service.create_card_payment(db, tenant_id, payload)


@router.get("/status/{order_id}", response_model=PaymentStatusRead)
async def get_payment_status(
    order_id: UUID,
    db: Any = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant),
    _staff: CurrentUser = Depends(get_current_staff),
) -> PaymentStatusRead:
    return await payment_service.get_payment_status(db, tenant_id, order_id)
