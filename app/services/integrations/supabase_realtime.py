from typing import Any

import httpx
from fastapi.encoders import jsonable_encoder

from app.core.config import Settings


def publish_realtime(event: str, payload: dict[str, Any], settings: Settings) -> bool:
    broadcast_url = settings.supabase_broadcast_url
    api_key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_ANON_KEY
    if not broadcast_url or not api_key:
        return False

    body = {
        "messages": [
            {
                "topic": settings.SUPABASE_REALTIME_CHANNEL,
                "event": event,
                "payload": jsonable_encoder(payload),
            }
        ]
    }
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        response = httpx.post(broadcast_url, json=body, headers=headers, timeout=5.0)
        return response.is_success
    except httpx.HTTPError:
        return False
