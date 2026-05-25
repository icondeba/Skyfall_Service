from typing import Any


class WhatsAppClient:
    async def send_message(self, phone: str, template: str, data: dict[str, Any]) -> bool:
        # TODO: wire Meta Cloud API transport.
        return bool(phone and template)


whatsapp_client = WhatsAppClient()
