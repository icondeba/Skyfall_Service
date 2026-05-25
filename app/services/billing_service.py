import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import DomainError
from app.core.logging import get_logger
from app.repositories.order_repository import order_repository
from app.repositories.table_repository import table_repository
from app.schemas.billing import BillingFinaliseRead, BillingRead
from app.services.invoice import generate_invoice_pdf
from app.services.payment_service import paid_amount, payment_status
from app.services.email import send_email_invoice
from app.services.integrations.supabase_realtime import publish_realtime
from app.services.sms import send_sms_invoice
from app.services.whatsapp import send_whatsapp_invoice

logger = get_logger("skyfall.billing")


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class BillingService:
    def _build_response(self, order: Any) -> BillingRead:
        paid = paid_amount(order)
        return BillingRead(
            order=order,
            invoice=order.invoice,
            items=order.items,
            payments=order.payments,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            paid_amount=paid,
            due_amount=round(max(order.total_amount - paid, 0.0), 2),
            payment_status=payment_status(order),
        )

    async def finalise(self, db: Any, tenant_id: UUID, order_id: UUID, billed_by_staff_id: UUID | None = None) -> BillingFinaliseRead:
        # Expire ALL session-cached objects before loading. When finalise() is called
        # within the same request as payment_service (same SQLAlchemy session), the
        # order's `payments` relationship is already marked "loaded" in the identity map
        # from an earlier get_with_items call. Even with selectinload in the new query,
        # SQLAlchemy skips the additional SELECT for a relationship it considers loaded.
        # expire_all() forces every attribute to reload from the DB on next access,
        # so the new payment flushed by payment_repository.create() becomes visible.
        db.expire_all()

        order = order_repository.get_with_items(db, tenant_id, order_id)
        if order is None:
            raise DomainError("Order not found", status_code=404, error_code="order_not_found")

        if payment_status(order) != "paid":
            raise DomainError(
                "Payment status must be success before billing can be finalised",
                status_code=400,
                error_code="payment_not_success",
            )

        should_count_visit = order.status != "served"
        # PDF generation is non-fatal: WeasyPrint / Supabase may be unconfigured in dev.
        # The order must be finalised regardless; fall back to the billing API URL.
        try:
            invoice_url = await generate_invoice_pdf(order.id, db, billed_by_staff_id=billed_by_staff_id)
        except Exception as exc:
            logger.warning("invoice generation skipped: %s", exc)
            invoice_url = f"/api/v1/billing/{order.id}"
        order.status = "served"
        # Flush "served" to the DB immediately so the count query below sees the
        # updated status. With autoflush=False this is required — without it the
        # SELECT inside count_active_for_table still sees the old status and
        # keeps the table as occupied.
        db.flush()
        if should_count_visit and order.customer is not None:
            order.customer.visit_count += 1
            order.customer.total_spent = round(order.customer.total_spent + order.total_amount, 2)
            order.customer.last_visit = utc_now()
        if order.table_id is not None and not order_repository.count_open_for_table(db, tenant_id, order.table_id):
            table_repository.update_status(db, tenant_id, order.table_id, "free")
        db.commit()

        refreshed = order_repository.get_with_items(db, tenant_id, order_id) or order
        customer = refreshed.customer
        table = refreshed.table
        phone = customer.phone if customer is not None else ""
        customer_name = customer.name if customer is not None else None
        customer_email = customer.email if customer is not None else None
        table_number = table.table_number if table is not None else None
        # Only send notifications on the first finalise; skip if order was already served
        # (re-finalise is idempotent but must not double-send invoices).
        if should_count_visit:
            if phone:
                asyncio.create_task(
                    send_whatsapp_invoice(phone, customer_name, refreshed.total_amount, invoice_url, table_number)
                )
                asyncio.create_task(send_sms_invoice(phone, refreshed.total_amount, invoice_url))
            if customer_email:
                asyncio.create_task(
                    send_email_invoice(customer_email, customer_name, refreshed.total_amount, invoice_url, table_number)
                )

        publish_realtime(
            "order.served",
            {
                "order_id": str(refreshed.id),
                "table_id": str(refreshed.table_id) if refreshed.table_id else None,
            },
            settings,
        )

        return BillingFinaliseRead(
            invoice_url=invoice_url,
            order_id=refreshed.id,
            total_amount=refreshed.total_amount,
            table_number=table_number,
        )

    async def get_bill(self, db: Any, tenant_id: UUID, order_id: UUID) -> BillingRead:
        order = order_repository.get_with_items(db, tenant_id, order_id)
        if order is None:
            raise DomainError("Order not found", status_code=404, error_code="order_not_found")
        return self._build_response(order)


billing_service = BillingService()
