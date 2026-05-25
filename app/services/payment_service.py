import json
from typing import Any
from urllib.parse import quote, urlencode
from uuid import UUID

from sqlalchemy import func, select

from app.core.config import settings
from app.core.exceptions import DomainError, InsufficientPaymentError, PaymentAlreadyCompletedError
from app.core.logging import get_logger
from app.models import Order, Payment
from app.repositories.order_repository import order_repository
from app.repositories.payment_repository import payment_repository
from app.schemas.payment import (
    CardPaymentRequest,
    CardPaymentResponse,
    CashPaymentRequest,
    CashPaymentResponse,
    PaymentRead,
    PaymentStatusRead,
    RazorpayCreateOrderRequest,
    RazorpayCreateOrderResponse,
    RazorpayWebhookResponse,
)
from app.services.integrations.razorpay import amount_to_subunits, create_gateway_order, verify_webhook_signature


def paid_amount(order: Any) -> float:
    return round(sum(payment.amount for payment in order.payments if payment.status == "success"), 2)


def payment_status(order: Any) -> str:
    paid = paid_amount(order)
    if paid <= 0:
        return "unpaid"
    if paid + 0.01 < order.total_amount:
        return "partial"
    return "paid"


def amount_from_paise(amount_in_paise: int) -> float:
    return round(amount_in_paise / 100, 2)


def invoice_url_for(order: Any) -> str | None:
    if getattr(order, "invoice", None) is not None and order.invoice.pdf_url:
        return order.invoice.pdf_url
    if getattr(order, "invoice", None) is not None:
        return f"/api/v1/billing/{order.id}"
    return None


class PaymentService:
    def _requested_gateway_amount(self, payload: RazorpayCreateOrderRequest, due_amount: float) -> float:
        if payload.amount_in_paise is not None:
            return amount_from_paise(payload.amount_in_paise)
        if payload.amount is not None:
            return round(payload.amount, 2)
        return due_amount

    def _upi_qr_value(self, order_id: UUID, amount: float) -> str:
        upi_vpa = getattr(settings, "UPI_VPA", "")
        payee_name = getattr(settings, "UPI_PAYEE_NAME", settings.CAFE_NAME)
        query = {
            "pn": payee_name,
            "am": f"{amount:.2f}",
            "cu": settings.CURRENCY,
            "tr": str(order_id),
            "tn": f"{settings.CAFE_NAME} order {str(order_id)[-6:]}",
        }
        if upi_vpa:
            query["pa"] = upi_vpa
        return f"upi://pay?{urlencode(query, quote_via=quote)}"

    async def _finalise_if_fully_paid(self, db: Any, tenant_id: UUID, order_id: UUID) -> Any | None:
        # Flush any in-memory changes (e.g. Razorpay sets payment.status in memory before
        # calling here) so the raw SQL aggregate below sees them within this transaction.
        db.flush()

        total = db.execute(
            select(Order.total_amount).where(Order.id == order_id)
        ).scalar_one_or_none()
        if total is None:
            return None
        paid = round(
            float(
                db.execute(
                    select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
                        Payment.order_id == order_id,
                        Payment.status == "success",
                    )
                ).scalar_one()
                or 0.0
            ),
            2,
        )
        if paid + 0.01 < float(total):
            return None

        # Commit the payment before calling billing_service.finalise(). This is the key fix:
        # when finalise() runs in the same SQLAlchemy session as payment creation, the
        # identity-map may serve a cached Order.payments list that doesn't include the new
        # payment — even after expire_all() + selectinload. By committing first, finalise()
        # starts in a fresh transaction and always loads the payment from committed DB state,
        # completely bypassing any ORM caching.
        db.commit()

        from app.services.billing_service import billing_service
        try:
            return await billing_service.finalise(db, tenant_id, order_id)
        except Exception as exc:
            # Payment is already committed. Log and return None so the caller can still
            # return a success response; the frontend auto-finalise will clean up.
            logger.warning("finalise failed after payment commit: %s", exc)
            return None

    async def create_razorpay_order(
        self,
        db: Any,
        tenant_id: UUID,
        payload: RazorpayCreateOrderRequest,
    ) -> RazorpayCreateOrderResponse:
        order = order_repository.get_with_items(db, tenant_id, payload.order_id)
        if order is None:
            raise DomainError("Order not found", status_code=404, error_code="order_not_found")
        due_amount = round(order.total_amount - paid_amount(order), 2)
        amount = self._requested_gateway_amount(payload, due_amount)
        if amount <= 0:
            raise PaymentAlreadyCompletedError("Order is already paid")
        if amount > due_amount + 0.01:
            raise InsufficientPaymentError("Payment amount cannot exceed order due amount")

        gateway_order = create_gateway_order(order.id, amount, payload.notes, settings)
        payment = payment_repository.create(
            db,
            tenant_id,
            {
                "order_id": order.id,
                "mode": "upi",
                "amount": amount,
                "status": "pending",
                "razorpay_order_id": gateway_order["id"],
            },
        )
        db.commit()
        db.refresh(payment)
        return RazorpayCreateOrderResponse(
            payment_id=payment.id,
            razorpay_order_id=payment.razorpay_order_id or gateway_order["id"],
            amount=amount_to_subunits(payment.amount),
            currency=settings.CURRENCY,
            key_id=settings.RAZORPAY_KEY_ID,
            qr_image_url=self._upi_qr_value(order.id, payment.amount),
            status=payment.status,
            gateway_response=gateway_order,
        )

    async def handle_razorpay_webhook(
        self,
        db: Any,
        tenant_id: UUID,
        body: bytes,
        signature: str | None,
    ) -> RazorpayWebhookResponse:
        if not verify_webhook_signature(body, signature, settings):
            return RazorpayWebhookResponse(received=True, event="invalid_signature")
        try:
            event_payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return RazorpayWebhookResponse(received=True, event="invalid_json")
        event = event_payload.get("event")
        payment_entity = event_payload.get("payload", {}).get("payment", {}).get("entity", {})
        gateway_order_id = payment_entity.get("order_id")
        gateway_payment_id = payment_entity.get("id")

        payment = None
        if gateway_order_id:
            payment = payment_repository.get_by_razorpay_order_id(db, tenant_id, gateway_order_id)
        if payment is not None:
            payment.razorpay_payment_id = gateway_payment_id
            if event in {"payment.captured", "order.paid"}:
                payment.status = "success"
                billing = await self._finalise_if_fully_paid(db, tenant_id, payment.order_id)
                if billing is None:
                    db.commit()
            elif event in {"payment.failed"}:
                payment.status = "failed"
                db.commit()
        return RazorpayWebhookResponse(
            received=True,
            updated_payment_id=payment.id if payment else None,
            event=event,
        )

    async def create_cash_payment(self, db: Any, tenant_id: UUID, payload: CashPaymentRequest) -> CashPaymentResponse:
        order = order_repository.get_with_items(db, tenant_id, payload.order_id)
        if order is None:
            raise DomainError("Order not found", status_code=404, error_code="order_not_found")
        due_amount = round(order.total_amount - paid_amount(order), 2)
        if due_amount <= 0:
            raise PaymentAlreadyCompletedError("Order is already paid")

        payment_amount = round(payload.amount if payload.amount is not None else due_amount, 2)
        amount_received = round(payload.amount_received if payload.amount_received is not None else payment_amount, 2)
        if payment_amount > due_amount + 0.01:
            raise InsufficientPaymentError("Payment amount cannot exceed order due amount")
        if amount_received + 0.01 < payment_amount:
            raise InsufficientPaymentError("Cash received is less than the payment amount")
        if payload.amount is None and paid_amount(order) <= 0 and amount_received + 0.01 < order.total_amount:
            raise InsufficientPaymentError("Cash received must cover the order total")

        payment = payment_repository.create(
            db,
            tenant_id,
            {
                "order_id": order.id,
                "mode": "cash",
                "amount": payment_amount,
                "status": "success",
            },
        )
        billing = await self._finalise_if_fully_paid(db, tenant_id, order.id)
        if billing is None:
            db.commit()
        db.refresh(payment)
        refreshed_order = order_repository.get_with_items(db, tenant_id, order.id) or order
        return CashPaymentResponse(
            change_amount=round(max(amount_received - payment_amount, 0.0), 2),
            invoice_url=invoice_url_for(refreshed_order),
            payment=PaymentRead.model_validate(payment),
        )

    async def create_card_payment(self, db: Any, tenant_id: UUID, payload: CardPaymentRequest) -> CardPaymentResponse:
        order = order_repository.get_with_items(db, tenant_id, payload.order_id)
        if order is None:
            raise DomainError("Order not found", status_code=404, error_code="order_not_found")
        due_amount = round(order.total_amount - paid_amount(order), 2)
        amount = round(payload.amount, 2)
        if due_amount <= 0:
            raise PaymentAlreadyCompletedError("Order is already paid")
        if amount > due_amount + 0.01:
            raise InsufficientPaymentError("Payment amount cannot exceed order due amount")

        payment = payment_repository.create(
            db,
            tenant_id,
            {
                "order_id": order.id,
                "mode": payload.mode,
                "amount": amount,
                "status": "success",
            },
        )
        billing = await self._finalise_if_fully_paid(db, tenant_id, order.id)
        if billing is None:
            db.commit()
        db.refresh(payment)
        refreshed_order = order_repository.get_with_items(db, tenant_id, order.id) or order
        return CardPaymentResponse(
            invoice_url=invoice_url_for(refreshed_order),
            payment=PaymentRead.model_validate(payment),
        )

    async def get_payment_status(self, db: Any, tenant_id: UUID, order_id: UUID) -> PaymentStatusRead:
        order = order_repository.get_with_items(db, tenant_id, order_id)
        if order is None:
            raise DomainError("Order not found", status_code=404, error_code="order_not_found")
        paid = paid_amount(order)
        latest = payment_repository.get_latest_for_order(db, tenant_id, order_id)
        aggregate_status = payment_status(order)
        top_level_status = latest.status if latest is not None else aggregate_status
        return PaymentStatusRead(
            order_id=order.id,
            mode=latest.mode if latest else None,
            status=top_level_status,
            razorpay_payment_id=latest.razorpay_payment_id if latest else None,
            paid_at=latest.created_at if latest and latest.status == "success" else None,
            amount=latest.amount if latest else 0.0,
            total_amount=order.total_amount,
            paid_amount=paid,
            due_amount=round(max(order.total_amount - paid, 0.0), 2),
            payments=order.payments,
        )


logger = get_logger("skyfall.payment")

payment_service = PaymentService()
