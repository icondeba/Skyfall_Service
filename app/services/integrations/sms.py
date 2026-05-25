class SMSClient:
    async def send_sms(self, phone: str, message: str) -> bool:
        # TODO: wire Twilio transport.
        return bool(phone and message)


sms_client = SMSClient()
