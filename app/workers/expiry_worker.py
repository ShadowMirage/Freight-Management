import asyncio
from datetime import datetime
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.booking import Booking
from app.models.truck import Truck
from app.models.load import Load
from app.models.enums import BookingStatus, PaymentStatus, FreightStatus
from app.whatsapp.logger import logger
import json

async def start_reservation_expiry_worker():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                now = datetime.utcnow()
                stmt = select(Booking).where(
                    Booking.payment_status == PaymentStatus.PAYMENT_PENDING,
                    Booking.payment_expires_at < now
                ).with_for_update(skip_locked=True)
                
                res = await db.execute(stmt)
                expired_bookings = res.scalars().all()
                
                for booking in expired_bookings:
                    booking.status = BookingStatus.EXPIRED
                    booking.payment_status = PaymentStatus.FAILED
                    
                    truck_stmt = select(Truck).where(Truck.id == booking.truck_id).with_for_update()
                    load_stmt = select(Load).where(Load.id == booking.load_id).with_for_update()
                    
                    truck = (await db.execute(truck_stmt)).scalars().first()
                    load = (await db.execute(load_stmt)).scalars().first()
                    
                    if truck and truck.status == FreightStatus.RESERVED:
                        truck.status = FreightStatus.OPEN
                    if load and load.status == FreightStatus.RESERVED:
                        load.status = FreightStatus.OPEN
                        
                    logger.info(json.dumps({
                        "action": "booking_expired",
                        "booking_id": str(booking.id),
                        "reference_id": booking.booking_reference_id
                    }))
                
                if expired_bookings:
                    await db.commit()
        except Exception as e:
            logger.error(f"Expiry worker error: {str(e)}")
            
        await asyncio.sleep(60)
