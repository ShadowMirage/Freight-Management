import json
import re
from datetime import datetime
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.whatsapp.logger import logger
from app.whatsapp.client import send_message
from app.services.conversation_service import conversation_service
from app.whatsapp.validators import PickupDropCityValidator, CapacityValidator, DateValidator
from app.models.truck import Truck
from app.services.truck_service import truck_service
from app.models.user import User, UserRole
from app.services.user_service import user_service

def is_reserved_command(text: str) -> bool:
    text_lower = text.lower().strip()
    return text_lower in ["post truck", "post load", "help"] or text_lower.startswith("book")

def is_cancel(text: str) -> bool:
    return text.lower().strip() == "cancel"

def validate_city(text: str) -> bool:
    return bool(re.match(r"^[A-Za-z ]{2,50}$", text.strip()))

def validate_capacity(text: str) -> bool:
    try:
        val = float(text.strip())
        return 0 < val <= 100
    except ValueError:
        return False

def validate_date(text: str) -> bool:
    try:
        dt = datetime.strptime(text.strip(), "%d-%m-%Y").date()
        return dt >= datetime.utcnow().date()
    except ValueError:
        return False

async def handle_conversation(phone: str, text: str, db: AsyncSession) -> None:
    session_obj = await conversation_service.get_active_session(db, phone)
    text_lower = text.lower().strip()

    # Pre-step guards for active sessions
    if session_obj:
        if is_cancel(text):
            await conversation_service.clear_session(db, phone)
            await send_message(phone, "Flow cancelled. You may type 'post truck' or 'post load' to begin again.")
            return
            
        if is_reserved_command(text):
            await send_message(phone, "⚠️ You are currently in an active flow. Please complete it or type CANCEL to restart.")
            return

        step = session_obj.current_step
        if step in ["pickup_city", "drop_city", "category"]:
            if not validate_city(text):
                await send_message(phone, "⚠️ Enter a valid city or category name (letters only). Example: Jaipur")
                return
        elif step in ["capacity_tons", "weight_tons"]:
            if not validate_capacity(text):
                await send_message(phone, "⚠️ Enter a valid number between 1 and 100.")
                return
        elif step in ["available_date", "pickup_date"]:
            if not validate_date(text):
                await send_message(phone, "⚠️ Enter a valid future date in format DD-MM-YYYY.")
                return

    # 1. No active session
    if not session_obj:
        if text_lower == "post truck":
            await conversation_service.start_session(db, phone, flow="post_truck", step="pickup_city")
            await send_message(phone, "Great! Let's post a truck. Please enter the pickup city:")
        elif text_lower == "post load":
            await conversation_service.start_session(db, phone, flow="post_load", step="pickup_city")
            await send_message(phone, "Great! Let's post a load. Please enter the pickup city:")
        elif text_lower == "help":
            await send_message(phone, "Welcome to Freight Matching! You can say 'post truck' or 'post load' to get started.")
        elif text_lower.startswith("book "):
            parts = text_lower.split()
            if len(parts) == 2 and parts[1].isdigit():
                index = int(parts[1])
                from app.whatsapp.memcache import PENDING_MATCHES
                pending = PENDING_MATCHES.get(phone)
                if not pending:
                    await send_message(phone, "⚠️ No active matches to book. Please post a load or truck first.")
                    return
                matches = pending.get("matches", [])
                if index < 1 or index > len(matches):
                    await send_message(phone, f"⚠️ Invalid selection. Please choose a number between 1 and {len(matches)}.")
                    return
                selected = matches[index - 1]
                
                await conversation_service.start_session(db, phone, flow="booking", step="confirm_booking")
                await conversation_service.update_step(db, phone, step="confirm_booking", new_data={
                    "my_type": pending["type"],
                    "my_id": pending["my_id"],
                    "match_id": selected["id"],
                    "details": selected["details"]
                })
                await send_message(phone, f"You selected:\n{selected['details']}\nReply CONFIRM to proceed or CANCEL to abort.")
            else:
                await send_message(phone, "I didn't quite understand that. Please reply with 'help' for instructions.")
        else:
            await send_message(phone, "I didn't quite understand that. Please reply with 'help' for instructions.")
        return

    # 2. Active session: post_truck flow
    if session_obj.current_flow == "post_truck":
        step = session_obj.current_step

        if step == "pickup_city":
            try:
                PickupDropCityValidator(city=text)
                await conversation_service.update_step(db, phone, step="drop_city", new_data={"pickup_city": text})
                await send_message(phone, "Got it. Now, please enter the drop city:")
            except ValidationError:
                logger.warning(json.dumps({"action": "validation_failed", "step": step, "phone": phone, "input": text}))
                await send_message(phone, "Invalid city. Must be at least 3 characters. Please enter the pickup city again:")

        elif step == "drop_city":
            try:
                PickupDropCityValidator(city=text)
                await conversation_service.update_step(db, phone, step="capacity_tons", new_data={"drop_city": text})
                await send_message(phone, "Perfect. What is the truck's capacity in tons? (e.g., 20)")
            except ValidationError:
                logger.warning(json.dumps({"action": "validation_failed", "step": step, "phone": phone, "input": text}))
                await send_message(phone, "Invalid city. Must be at least 3 characters. Please enter the drop city again:")

        elif step == "capacity_tons":
            try:
                val = CapacityValidator(capacity=int(text))
                await conversation_service.update_step(db, phone, step="available_date", new_data={"capacity_tons": val.capacity})
                await send_message(phone, "Noted. When is the truck available? Please use the format DD-MM-YYYY:")
            except (ValueError, ValidationError):
                logger.warning(json.dumps({"action": "validation_failed", "step": step, "phone": phone, "input": text}))
                await send_message(phone, "Invalid capacity. Must be a number between 1 and 100. Please enter the capacity again:")

        elif step == "available_date":
            try:
                val = DateValidator(date_str=text)
                date_obj = datetime.strptime(val.date_str, "%d-%m-%Y")
                
                # Validation passed, finalize creation
                final_data = session_obj.collected_data
                
                # Check if user exists, else create
                result = await db.execute(select(User).where(User.phone_number == phone))
                user = result.scalars().first()
                if not user:
                    from app.schemas.user import UserCreate
                    user = await user_service.create(db=db, obj_in=UserCreate(phone_number=phone, role=UserRole.DRIVER))
                
                # Create Truck
                from app.schemas.truck import TruckCreate
                truck_in = TruckCreate(
                    driver_id=user.id,
                    source_city=final_data["pickup_city"],
                    destination_city=final_data["drop_city"],
                    source_lat=0.0, # Placeholder until PostGIS Geocoding
                    source_lng=0.0,
                    dest_lat=0.0,
                    dest_lng=0.0,
                    departure_time=date_obj,
                    capacity_total=float(final_data["capacity_tons"]),
                    capacity_available=float(final_data["capacity_tons"])
                )
                truck, matches = await truck_service.create_with_matches(db=db, obj_in=truck_in)
                
                logger.info(json.dumps({
                    "action": "truck_created_with_matches",
                    "phone": phone,
                    "truck_id": str(truck.id),
                    "matches_found": len(matches)
                }))
                
                # Clear session
                await conversation_service.clear_session(db, phone)
                await send_message(phone, "Truck posted successfully ✅")
                
                # Format Matches and send
                from app.whatsapp.formatters import format_truck_matches
                from app.whatsapp.memcache import PENDING_MATCHES
                
                if matches:
                    PENDING_MATCHES[phone] = {
                        "type": "truck",
                        "my_id": str(truck.id),
                        "matches": [{"id": str(m.id), "details": f"{m.weight} tons - {m.pickup_city} -> {m.drop_city} - {m.deadline.strftime('%d-%m-%Y')}"} for m in matches]
                    }
                await send_message(phone, format_truck_matches(matches))
                
            except ValidationError as e:
                err_msg = e.errors()[0].get('msg', 'Invalid Date')
                logger.warning(json.dumps({"action": "validation_failed", "step": step, "phone": phone, "error": err_msg}))
                await send_message(phone, f"{err_msg}. Please enter the available date (DD-MM-YYYY) again:")

    # 3. Active session: post_load flow
    elif session_obj.current_flow == "post_load":
        step = session_obj.current_step

        if step == "pickup_city":
            try:
                PickupDropCityValidator(city=text)
                await conversation_service.update_step(db, phone, step="drop_city", new_data={"pickup_city": text})
                await send_message(phone, "Got it. Now, please enter the drop city:")
            except ValidationError:
                logger.warning(json.dumps({"action": "validation_failed", "step": step, "phone": phone, "input": text}))
                await send_message(phone, "Invalid city. Must be at least 3 characters. Please enter the pickup city again:")

        elif step == "drop_city":
            try:
                PickupDropCityValidator(city=text)
                await conversation_service.update_step(db, phone, step="weight_tons", new_data={"drop_city": text})
                await send_message(phone, "Perfect. What is the load's weight in tons? (e.g., 20)")
            except ValidationError:
                logger.warning(json.dumps({"action": "validation_failed", "step": step, "phone": phone, "input": text}))
                await send_message(phone, "Invalid city. Must be at least 3 characters. Please enter the drop city again:")

        elif step == "weight_tons":
            try:
                val = CapacityValidator(capacity=int(text))
                await conversation_service.update_step(db, phone, step="category", new_data={"weight_tons": val.capacity})
                await send_message(phone, "Noted. What is the category of the load? (e.g., General, Electronics):")
            except (ValueError, ValidationError):
                logger.warning(json.dumps({"action": "validation_failed", "step": step, "phone": phone, "input": text}))
                await send_message(phone, "Invalid weight. Must be a number between 1 and 100. Please enter the weight again:")

        elif step == "category":
            await conversation_service.update_step(db, phone, step="pickup_date", new_data={"category": text.strip()})
            await send_message(phone, "Got it. When is the pickup date? Please use the format DD-MM-YYYY:")

        elif step == "pickup_date":
            try:
                val = DateValidator(date_str=text)
                date_obj = datetime.strptime(val.date_str, "%d-%m-%Y")
                
                # Validation passed, finalize creation
                final_data = session_obj.collected_data
                
                # Check if user exists, else create
                result = await db.execute(select(User).where(User.phone_number == phone))
                user = result.scalars().first()
                if not user:
                    from app.schemas.user import UserCreate
                    user = await user_service.create(db=db, obj_in=UserCreate(phone_number=phone, role=UserRole.SHIPPER))
                
                # Create Load
                from app.schemas.load import LoadCreate
                from app.services.load_service import load_service
                load_in = LoadCreate(
                    shipper_id=user.id,
                    pickup_city=final_data["pickup_city"],
                    drop_city=final_data["drop_city"],
                    pickup_lat=0.0,
                    pickup_lng=0.0,
                    drop_lat=0.0,
                    drop_lng=0.0,
                    deadline=date_obj,
                    weight=float(final_data["weight_tons"]),
                    category=final_data["category"]
                )
                load, matches = await load_service.create_with_matches(db=db, obj_in=load_in)
                
                logger.info(json.dumps({
                    "action": "load_created_with_matches",
                    "phone": phone,
                    "load_id": str(load.id),
                    "matches_found": len(matches)
                }))
                
                # Clear session
                await conversation_service.clear_session(db, phone)
                await send_message(phone, "Load posted successfully ✅")
                
                # Format Matches and send
                from app.whatsapp.formatters import format_load_matches
                from app.whatsapp.memcache import PENDING_MATCHES
                
                if matches:
                    PENDING_MATCHES[phone] = {
                        "type": "load",
                        "my_id": str(load.id),
                        "matches": [{"id": str(m.id), "details": f"{m.capacity_available} tons - {m.source_city} -> {m.destination_city} - {m.departure_time.strftime('%d-%m-%Y')}"} for m in matches]
                    }
                await send_message(phone, format_load_matches(matches))
                
            except ValidationError as e:
                err_msg = e.errors()[0].get('msg', 'Invalid Date')
                logger.warning(json.dumps({"action": "validation_failed", "step": step, "phone": phone, "error": err_msg}))
                await send_message(phone, f"{err_msg}. Please enter the pickup date (DD-MM-YYYY) again:")

    # 4. Active session: booking flow
    elif session_obj.current_flow == "booking":
        step = session_obj.current_step
        if step == "confirm_booking":
            if text_lower == "confirm":
                data = session_obj.collected_data
                from app.services.booking_service import booking_service
                import uuid
                
                try:
                    truck_id = uuid.UUID(data["my_id"] if data["my_type"] == "truck" else data["match_id"])
                    load_id = uuid.UUID(data["match_id"] if data["my_type"] == "truck" else data["my_id"])
                    
                    booking, error = await booking_service.create_atomic_booking(db, truck_id, load_id, 0.0)
                    if error:
                        await send_message(phone, f"⚠️ Booking failed: {error}")
                    else:
                        await send_message(phone, "Booking reserved successfully.\nPayment link will be generated shortly.")
                except Exception as e:
                    logger.error(f"Booking error: {str(e)}")
                    await send_message(phone, "⚠️ An error occurred while creating booking.")
                    
                await conversation_service.clear_session(db, phone)
                from app.whatsapp.memcache import PENDING_MATCHES
                PENDING_MATCHES.pop(phone, None)
            else:
                await send_message(phone, "⚠️ Please reply CONFIRM to proceed or CANCEL to abort.")
