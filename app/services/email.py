from __future__ import annotations

import asyncio
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("skyfall.email")


def _build_invoice_html(customer_name: str | None, total: float, pdf_url: str, table_no: int | str | None) -> str:
    name = customer_name or "Valued Guest"
    table = f"Table {table_no}" if table_no is not None else "Takeaway"
    return f"""
    <div style="font-family:Georgia,serif;max-width:520px;margin:0 auto;padding:28px 24px;background:#FAFAF7;border:1px solid #E8DBBF;border-radius:8px">
      <h2 style="color:#B8923A;margin:0 0 6px;font-size:22px">Skyfall Lounge</h2>
      <p style="color:#7A7060;font-size:13px;margin:0 0 20px">Thank you for your visit!</p>
      <p style="color:#1A1A1A;font-size:15px">Hi {name},</p>
      <p style="color:#1A1A1A;font-size:15px">
        Your bill of <strong style="color:#B8923A">₹{total:,.2f}</strong> for <strong>{table}</strong> has been settled.
        Please find your invoice linked below.
      </p>
      <a href="{pdf_url}"
         style="display:inline-block;margin:16px 0;padding:12px 24px;background:#B8923A;color:#FFFFFF;text-decoration:none;border-radius:6px;font-size:14px;font-weight:600">
        Download Invoice
      </a>
      <p style="color:#7A7060;font-size:12px;margin:20px 0 0">
        We hope to see you again soon at Skyfall Lounge.
      </p>
    </div>
    """


def _send_smtp(to_email: str, subject: str, html_body: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        logger.warning("email skipped: SMTP is not configured")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        server.starttls(context=context)
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())


async def send_email_invoice(
    email: str,
    customer_name: str | None,
    total: float,
    pdf_url: str,
    table_no: int | str | None,
) -> None:
    if not email:
        logger.warning("email skipped: no email address")
        return

    subject = f"Your Skyfall Lounge Invoice – ₹{total:,.2f}"
    html_body = _build_invoice_html(customer_name, total, pdf_url, table_no)
    try:
        await asyncio.to_thread(_send_smtp, email, subject, html_body)
        logger.info("email invoice sent", extra={"extra_fields": {"to": email}})
    except Exception as exc:
        logger.exception("email invoice failed", extra={"extra_fields": {"to": email, "error": str(exc)}})
