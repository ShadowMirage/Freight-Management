from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.booking import Booking
from app.models.truck import Truck
from app.models.load import Load
from app.models.enums import BookingStatus, PaymentStatus, FreightStatus
import json
from app.whatsapp.logger import logger

router = APIRouter()

class PaymentWebhookPayload(BaseModel):
    reference_id: str
    status: str

@router.post("/webhook")
async def handle_payment_webhook(payload: PaymentWebhookPayload, db: AsyncSession = Depends(get_db)):
    if payload.status != "PAID":
        return {"status": "ignored"}
        
    booking_stmt = select(Booking).where(Booking.booking_reference_id == payload.reference_id).with_for_update()
    res = await db.execute(booking_stmt)
    booking = res.scalars().first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if booking.payment_status == PaymentStatus.PAYMENT_PENDING:
        truck_stmt = select(Truck).where(Truck.id == booking.truck_id).with_for_update()
        load_stmt = select(Load).where(Load.id == booking.load_id).with_for_update()
        
        truck = (await db.execute(truck_stmt)).scalars().first()
        load = (await db.execute(load_stmt)).scalars().first()
        
        if truck and load:
            booking.payment_status = PaymentStatus.PAID
            booking.status = BookingStatus.PAID
            truck.status = FreightStatus.BOOKED
            load.status = FreightStatus.BOOKED
            
            await db.commit()
            
            logger.info(json.dumps({
                "action": "payment_processed",
                "reference_id": payload.reference_id,
                "booking_id": str(booking.id)
            }))
            return {"status": "success"}
    return {"status": "idempotent"}
