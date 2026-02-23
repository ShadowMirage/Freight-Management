import uuid
import hashlib
from typing import Tuple, Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.booking import Booking
from app.models.truck import Truck
from app.models.load import Load
from app.models.enums import BookingStatus, PaymentStatus, FreightStatus
from app.schemas.booking import BookingCreate, BookingUpdate
from app.services.base import CRUDBase

class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    async def create_atomic_booking(
        self,
        db: AsyncSession,
        truck_id: uuid.UUID,
        load_id: uuid.UUID,
        price: float
    ) -> Tuple[Optional[Booking], Optional[str]]:
        # Deterministic Idempotency Reference 
        # (Concatenates truck and load ID to prevent duplicate exact pairings in quick succession)
        raw_ref = f"{truck_id}_{load_id}"
        reference_id = f"BKG-{hashlib.md5(raw_ref.encode()).hexdigest()[:8].upper()}"
        
        # Immediate Idempotency Check
        existing_stmt = select(Booking).where(Booking.booking_reference_id == reference_id)
        existing_res = await db.execute(existing_stmt)
        existing_booking = existing_res.scalars().first()
        if existing_booking:
            return existing_booking, None

        # Lock rows
        truck_stmt = select(Truck).where(Truck.id == truck_id).with_for_update()
        load_stmt = select(Load).where(Load.id == load_id).with_for_update()
        
        truck_res = await db.execute(truck_stmt)
        truck = truck_res.scalars().first()
        
        load_res = await db.execute(load_stmt)
        load = load_res.scalars().first()
        
        if not truck or not load:
            await db.rollback()
            return None, "Invalid Truck or Load."
            
        if truck.status != FreightStatus.OPEN or load.status != FreightStatus.OPEN:
            await db.rollback()
            return None, "Truck or Load is no longer available."
            
        booking = Booking(
            truck_id=truck.id,
            load_id=load.id,
            price=price,
            status=BookingStatus.INITIATED,
            payment_status=PaymentStatus.PAYMENT_PENDING,
            booking_reference_id=reference_id,
            payment_link=f"https://pay.freight.local/checkout/{reference_id}",
            payment_reference_id=None,
            payment_expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        truck.status = FreightStatus.RESERVED
        load.status = FreightStatus.RESERVED
        
        db.add(booking)
        db.add(truck)
        db.add(load)
        
        await db.commit()
        await db.refresh(booking)
        
        return booking, None

booking_service = CRUDBooking(Booking)
