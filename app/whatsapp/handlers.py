import json
from app.whatsapp.logger import logger
from app.whatsapp.client import send_message

async def handle_post_truck(phone: str, text: str) -> None:
    logger.info(json.dumps({
        "action": "handle_post_truck",
        "phone": phone,
        "text": text
    }))
    await send_message(phone, "Thank you! We received your request to post a truck. A matching load will be found soon.")

async def handle_post_load(phone: str, text: str) -> None:
    logger.info(json.dumps({
        "action": "handle_post_load",
        "phone": phone,
        "text": text
    }))
    await send_message(phone, "Thank you! We received your request to post a load. A matching truck will be found soon.")

async def handle_help(phone: str) -> None:
    logger.info(json.dumps({
        "action": "handle_help",
        "phone": phone
    }))
    await send_message(phone, "Welcome to Freight Matching! You can say 'post truck' or 'post load' to get started.")

async def handle_unknown(phone: str) -> None:
    logger.info(json.dumps({
        "action": "handle_unknown",
        "phone": phone
    }))
    await send_message(phone, "I didn't quite understand that. Please reply with 'help' for instructions.")

async def handle_booking_selection(phone: str, selection_index: int) -> None:
    logger.info(json.dumps({
        "action": "booking_attempt",
        "phone": phone,
        "selection": selection_index
    }))
    await send_message(phone, f"Noted. Your request to book option {selection_index} has been received. Our team will resolve this shortly.")
