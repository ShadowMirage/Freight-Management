from pywa import WhatsApp
from app.core.config import settings

# Initialize PyWa client
wa = WhatsApp(
    phone_id=settings.WHATSAPP_PHONE_NUMBER_ID,
    token=settings.WHATSAPP_TOKEN
)

async def send_message(phone: str, text: str) -> None:
    """Helper to send a WhatsApp text message."""
    wa.send_message(
        to=phone,
        text=text
    )
