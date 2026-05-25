from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("skyfall.whatsapp")


def _recipient(phone: str) -> str:
    return phone.strip().replace(" ", "").replace("-", "").lstrip("+")


async def _post_message(payload: dict[str, Any]) -> bool:
    if not settings.META_WA_PHONE_ID or not settings.META_WA_TOKEN:
        logger.warning("whatsapp skipped: Meta Cloud API is not configured")
        return False

    url = f"https://graph.facebook.com/v18.0/{settings.META_WA_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.META_WA_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.is_success:
                logger.info("whatsapp message sent", extra={"extra_fields": {"status_code": response.status_code}})
                return True
            logger.error(
                "whatsapp message failed",
                extra={"extra_fields": {"status_code": response.status_code, "response": response.text[:500]}},
            )
            return False
    except httpx.HTTPError as exc:
        logger.exception("whatsapp transport failed", extra={"extra_fields": {"error": str(exc)}})
        return False


async def send_whatsapp_invoice(phone: str, customer_name: str | None, total: float, pdf_url: str, table_no: int | str | None) -> None:
    try:
        to = _recipient(phone)
        if not to:
            logger.warning("whatsapp skipped: phone number missing")
            return

        name = customer_name or "there"
        table = table_no if table_no is not None else "-"
        text_payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": (
                    f"Hi {name}! Thank you for visiting Skyfall Lounge.\n"
                    f"Your bill of Rs {total:,.2f} for Table {table} is ready. Here is your invoice:"
                ),
            },
        }
        document_payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": {
                "link": pdf_url,
                "filename": "Skyfall-Invoice.pdf",
            },
        }

        text_ok = await _post_message(text_payload)
        document_ok = await _post_message(document_payload)
        if text_ok and document_ok:
            logger.info("whatsapp invoice delivery completed", extra={"extra_fields": {"phone": to}})
        else:
            logger.error("whatsapp invoice delivery incomplete", extra={"extra_fields": {"phone": to}})
    except Exception as exc:
        logger.exception("whatsapp invoice delivery failed", extra={"extra_fields": {"phone": phone, "error": str(exc)}})
