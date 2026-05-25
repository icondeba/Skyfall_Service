from __future__ import annotations

import asyncio

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("skyfall.sms")


async def send_sms_invoice(phone: str, total: float, pdf_url: str) -> None:
    if not phone:
        logger.warning("sms skipped: phone number missing")
        return
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_PHONE_NUMBER:
        logger.warning("sms skipped: Twilio is not configured")
        return

    body = f"Skyfall Lounge invoice: total Rs {total:,.2f}. View/download your invoice: {pdf_url}"
    try:
        from twilio.rest import Client
    except ImportError:
        logger.exception("sms skipped: twilio package is not installed")
        return

    def _send() -> str:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone,
        )
        return str(message.sid)

    try:
        sid = await asyncio.to_thread(_send)
        logger.info("sms invoice sent", extra={"extra_fields": {"sid": sid, "phone": phone}})
    except Exception as exc:
        logger.exception("sms invoice failed", extra={"extra_fields": {"phone": phone, "error": str(exc)}})
