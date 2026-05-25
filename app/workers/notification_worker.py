from app.services.integrations.sms import sms_client
from app.services.integrations.whatsapp import whatsapp_client


async def send_bill_notifications(phone: str, message: str) -> dict[str, bool]:
    sms_sent = await sms_client.send_sms(phone, message)
    whatsapp_sent = await whatsapp_client.send_message(phone, "bill_ready", {"message": message})
    return {"sms_sent": sms_sent, "whatsapp_sent": whatsapp_sent}
