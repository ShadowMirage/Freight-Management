from typing import Any
from fastapi import APIRouter, Request, Response, HTTPException
import json
from app.core.config import settings
from app.whatsapp.logger import logger
from app.whatsapp.router import route_intent

router = APIRouter()

@router.get("/webhook")
async def verify_webhook(request: Request) -> Response:
    """
    Used for Meta verification handshake
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info(json.dumps({"action": "webhook_verified"}))
        return Response(content=challenge, status_code=200)
    
    logger.warning(json.dumps({"action": "webhook_verification_failed"}))
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request) -> Any:
    """
    Used for incoming WhatsApp message events
    """
    try:
        data = await request.json()
    except ValueError:
        return Response(status_code=400)
        
    logger.info(json.dumps({
        "action": "incoming_webhook",
        "payload": data
    }))

    if data.get("object") == "whatsapp_business_account":
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                
                for message in messages:
                    # Ignore non-text messages
                    if message.get("type") != "text":
                        continue
                        
                    phone = message.get("from")
                    text = message.get("text", {}).get("body")
                    
                    if phone and text:
                        logger.info(json.dumps({
                            "action": "message_parsed",
                            "phone": phone,
                            "text": text
                        }))
                        # Route message to intent
                        await route_intent(phone, text)

    return Response(content="OK", status_code=200)
