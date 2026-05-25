from __future__ import annotations

import asyncio
from datetime import datetime
from html import escape
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import DomainError
from app.core.logging import get_logger
from app.models import Invoice, Order, OrderItem

logger = get_logger("skyfall.invoice")

INVOICE_BUCKET = "invoices"
INVOICE_PATH_PREFIX = "skyfall-invoices"


def _money(amount: float | int | None) -> str:
    return f"Rs {float(amount or 0):,.2f}"


def _plain(value: Any, fallback: str = "-") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return escape(text) if text else fallback


def _invoice_number(db: Any, order: Order) -> str:
    year = (order.created_at or datetime.utcnow()).year
    start = datetime(year, 1, 1)
    end = datetime(year + 1, 1, 1)
    count = int(
        db.scalar(
            select(func.count(Invoice.id)).where(
                Invoice.created_at >= start,
                Invoice.created_at < end,
            )
        )
        or 0
    )
    return f"SKY-INV-{year}-{count + 1:04d}"


def _latest_success_payment(order: Order) -> Any | None:
    successful = [payment for payment in order.payments if payment.status == "success"]
    if not successful:
        return None
    return max(successful, key=lambda payment: payment.created_at)


def _payment_line(order: Order) -> str:
    payment = _latest_success_payment(order)
    if payment is None:
        return ""
    mode = {
        "upi": "UPI",
        "cash": "Cash",
        "debit_card": "Debit Card",
        "credit_card": "Credit Card",
    }.get(payment.mode, payment.mode.replace("_", " ").title())
    paid_at = payment.created_at.strftime("%I:%M %p").lstrip("0") if hasattr(payment.created_at, "strftime") else ""
    return f"Paid via {mode} . {paid_at}"


def _format_addons(addons: list[dict[str, Any]] | None) -> str:
    if not addons:
        return "-"
    return ", ".join(_plain(addon.get("name"), "") for addon in addons if addon.get("name")) or "-"


def _render_items(items: list[OrderItem]) -> str:
    rows: list[str] = []
    for index, item in enumerate(items):
        bg = "#FFFFFF" if index % 2 == 0 else "#FAFAF7"
        total = item.unit_price * item.quantity
        rows.append(
            f"""
            <tr style="background:{bg}; color:#2F2A24; font-size:11px;">
                <td style="padding:8px 6px; border-bottom:1px solid #EFE9DD;">{_plain(item.menu_item.name if item.menu_item else None)}</td>
                <td style="padding:8px 6px; border-bottom:1px solid #EFE9DD;">{_plain(item.variant.name if item.variant else None)}</td>
                <td style="padding:8px 6px; border-bottom:1px solid #EFE9DD;">{_format_addons(item.addons_json)}</td>
                <td style="padding:8px 6px; border-bottom:1px solid #EFE9DD; text-align:center;">{item.quantity}</td>
                <td style="padding:8px 6px; border-bottom:1px solid #EFE9DD; text-align:right;">{_money(item.unit_price)}</td>
                <td style="padding:8px 6px; border-bottom:1px solid #EFE9DD; text-align:right;">{_money(total)}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def _render_invoice_html(order: Order, invoice: Invoice) -> str:
    created = order.created_at or datetime.utcnow()
    table_number = order.table.table_number if order.table else "-"
    customer_name = order.customer.name if order.customer and order.customer.name else "Guest"
    cgst = round(order.tax_amount / 2, 2)
    sgst = round(order.tax_amount / 2, 2)
    discount = round(order.discount_amount or 0, 2)
    payment_line = _payment_line(order)
    cafe_address = _plain(getattr(settings, "CAFE_ADDRESS", ""), "Skyfall Lounge")
    cafe_gstin = _plain(getattr(settings, "CAFE_GSTIN", ""), "GSTIN: -")
    cafe_phone = _plain(getattr(settings, "CAFE_PHONE", ""), "Phone: -")
    social_handles = _plain(getattr(settings, "CAFE_SOCIAL_HANDLES", ""), "@skyfalllounge")

    discount_row = ""
    if discount > 0:
        discount_row = f"""
            <tr>
                <td style="padding:4px 0; color:#A43D2E;">Discount</td>
                <td style="padding:4px 0; text-align:right; color:#A43D2E;">-{_money(discount)}</td>
            </tr>
        """

    payment_block = ""
    if payment_line:
        payment_block = f"""
            <div style="margin-top:14px; color:#2F8A4C; font-size:10px;">
                {_plain(payment_line)}
            </div>
        """

    return f"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{_plain(invoice.invoice_number)}</title>
    </head>
    <body style="margin:0; padding:28px; font-family:Arial, Helvetica, sans-serif; color:#2F2A24; background:#FFFFFF;">
        <div style="text-align:center; font-family:Georgia, 'Times New Roman', serif; font-size:28px; color:#B8923A; letter-spacing:0;">
            SKYFALL LOUNGE
        </div>
        <div style="margin-top:5px; text-align:center; font-size:10px; color:#7A7060; line-height:1.45;">
            {cafe_address}<br>
            {cafe_gstin} &nbsp; {cafe_phone}
        </div>

        <div style="margin-top:24px; display:block; text-align:right; font-size:10px; color:#4A433B; line-height:1.6;">
            <div>Invoice No: {_plain(invoice.invoice_number)}</div>
            <div>Date: {created.strftime("%d %b %Y")}</div>
            <div>Time: {created.strftime("%I:%M %p")}</div>
            <div>Table: {_plain(table_number)}</div>
            <div>Order ID: {_plain(order.id)}</div>
        </div>

        <div style="margin-top:18px; text-align:center; font-size:11px; text-transform:uppercase; letter-spacing:2px; color:#B8923A;">
            INVOICE
        </div>
        <div style="margin-top:8px; font-size:11px; color:#4A433B;">
            Customer: {_plain(customer_name)}
        </div>

        <table style="margin-top:14px; width:100%; border-collapse:collapse;">
            <thead>
                <tr style="background:#F7EDD8; color:#8A6A24; font-size:10px; text-transform:uppercase;">
                    <th style="padding:8px 6px; text-align:left;">Item</th>
                    <th style="padding:8px 6px; text-align:left;">Variant</th>
                    <th style="padding:8px 6px; text-align:left;">Add-ons</th>
                    <th style="padding:8px 6px; text-align:center;">Qty</th>
                    <th style="padding:8px 6px; text-align:right;">Unit Price</th>
                    <th style="padding:8px 6px; text-align:right;">Total</th>
                </tr>
            </thead>
            <tbody>
                {_render_items(order.items)}
            </tbody>
        </table>

        <div style="margin-top:16px; margin-left:auto; max-width:200px; font-size:11px;">
            <table style="width:100%; border-collapse:collapse;">
                <tr>
                    <td style="padding:4px 0;">Subtotal</td>
                    <td style="padding:4px 0; text-align:right;">{_money(order.subtotal)}</td>
                </tr>
                <tr>
                    <td style="padding:4px 0;">CGST 2.5%</td>
                    <td style="padding:4px 0; text-align:right;">{_money(cgst)}</td>
                </tr>
                <tr>
                    <td style="padding:4px 0;">SGST 2.5%</td>
                    <td style="padding:4px 0; text-align:right;">{_money(sgst)}</td>
                </tr>
                {discount_row}
                <tr>
                    <td style="padding:8px 0 4px; border-top:1px solid #E8DBBF; font-weight:bold; font-size:14px; color:#B8923A;">GRAND TOTAL</td>
                    <td style="padding:8px 0 4px; border-top:1px solid #E8DBBF; text-align:right; font-weight:bold; font-size:14px; color:#B8923A;">{_money(order.total_amount)}</td>
                </tr>
            </table>
        </div>

        {payment_block}

        <div style="margin-top:34px; text-align:center;">
            <div style="font-style:italic; color:#B8923A; font-size:12px;">Thank you for visiting Skyfall Lounge</div>
            <div style="margin-top:6px; color:#7A7060; font-size:10px;">{social_handles} &nbsp; | &nbsp; Visit us again soon</div>
        </div>
    </body>
    </html>
    """


def _public_invoice_url(path: str) -> str:
    return f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{INVOICE_BUCKET}/{path}"


async def _upload_invoice_pdf(path: str, pdf_bytes: bytes) -> str:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise DomainError(
            "Supabase storage is not configured for invoice upload",
            status_code=500,
            error_code="invoice_storage_not_configured",
        )

    upload_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{INVOICE_BUCKET}/{path}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Content-Type": "application/pdf",
        "x-upsert": "true",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(upload_url, content=pdf_bytes, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception(
            "invoice upload failed",
            extra={"extra_fields": {"path": path, "order_id": path.rsplit("/", 1)[-1]}},
        )
        raise DomainError(
            "Failed to upload invoice PDF",
            status_code=502,
            error_code="invoice_upload_failed",
        ) from exc
    return _public_invoice_url(path)


async def generate_invoice_pdf(order_id: UUID, db: Any, billed_by_staff_id: UUID | None = None) -> str:
    statement = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.menu_item),
            selectinload(Order.items).selectinload(OrderItem.variant),
            selectinload(Order.payments),
            selectinload(Order.invoice),
            selectinload(Order.customer),
            selectinload(Order.table),
        )
    )
    order = db.scalar(statement)
    if order is None:
        raise DomainError("Order not found", status_code=404, error_code="order_not_found")

    invoice = order.invoice
    if invoice is None:
        invoice = Invoice(order_id=order.id, invoice_number=_invoice_number(db, order))
        db.add(invoice)
        db.flush()
    if billed_by_staff_id is not None and invoice.billed_by_staff_id is None:
        invoice.billed_by_staff_id = billed_by_staff_id

    html = _render_invoice_html(order, invoice)
    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise DomainError(
            "WeasyPrint is not installed",
            status_code=500,
            error_code="invoice_pdf_dependency_missing",
        ) from exc

    try:
        pdf_bytes = await asyncio.to_thread(lambda: HTML(string=html).write_pdf())
    except Exception as exc:
        logger.exception(
            "invoice pdf generation failed",
            extra={"extra_fields": {"order_id": str(order_id), "invoice_number": invoice.invoice_number}},
        )
        raise DomainError(
            "Failed to generate invoice PDF",
            status_code=500,
            error_code="invoice_pdf_generation_failed",
        ) from exc

    storage_path = f"{INVOICE_PATH_PREFIX}/{order_id}.pdf"
    pdf_url = await _upload_invoice_pdf(storage_path, pdf_bytes)
    invoice.pdf_url = pdf_url
    db.flush()
    logger.info(
        "invoice generated",
        extra={"extra_fields": {"order_id": str(order_id), "invoice_number": invoice.invoice_number}},
    )
    return pdf_url
