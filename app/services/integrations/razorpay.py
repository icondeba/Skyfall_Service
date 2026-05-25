import hmac
import uuid
from hashlib import sha256
from typing import Any

from app.core.config import Settings, settings


def amount_to_subunits(amount: float) -> int:
    return int(round(amount * 100))


def is_real_razorpay_config(config: Settings = settings) -> bool:
    return bool(
        config.RAZORPAY_KEY_ID
        and config.RAZORPAY_KEY_SECRET
        and "your" not in config.RAZORPAY_KEY_ID.lower()
        and "your" not in config.RAZORPAY_KEY_SECRET.lower()
    )


def create_gateway_order(
    order_id: uuid.UUID,
    amount: float,
    notes: dict[str, str],
    config: Settings = settings,
) -> dict[str, Any]:
    amount_subunits = amount_to_subunits(amount)
    data = {
        "amount": amount_subunits,
        "currency": config.CURRENCY,
        "receipt": str(order_id),
        "notes": {"order_id": str(order_id), **notes},
    }
    if not is_real_razorpay_config(config):
        return {
            "id": f"order_dev_{uuid.uuid4().hex}",
            "amount": amount_subunits,
            "currency": config.CURRENCY,
            "status": "created",
            "receipt": str(order_id),
            "notes": data["notes"],
        }

    import razorpay

    client = razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))
    return client.order.create(data=data)


def verify_webhook_signature(
    body: bytes,
    signature: str | None,
    config: Settings = settings,
) -> bool:
    if not config.RAZORPAY_WEBHOOK_SECRET:
        return True
    if not signature:
        return False
    expected = hmac.new(
        config.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        body,
        sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
