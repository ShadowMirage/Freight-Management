import json
from app.whatsapp.logger import logger
from app.whatsapp.handlers import (
    handle_post_truck,
    handle_post_load,
    handle_help,
    handle_unknown
)

async def route_intent(phone: str, text: str) -> None:
    text_lower = text.lower().strip()
    
    # Simple regex-less intent matching for now
    if "post truck" in text_lower:
        intent = "post_truck"
        await handle_post_truck(phone, text)
    elif "post load" in text_lower:
        intent = "post_load"
        await handle_post_load(phone, text)
    elif "help" in text_lower:
        intent = "help"
        await handle_help(phone)
    else:
        intent = "unknown"
        await handle_unknown(phone)
        
    logger.info(json.dumps({
        "action": "intent_routed",
        "phone": phone,
        "intent_detected": intent
    }))
