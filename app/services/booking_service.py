from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.booking import Booking
from app.models.truck import Truck
from app.models.load import Load
from app.schemas.booking import BookingCreate, BookingUpdate
from app.services.base import CRUDBase
import uuid
from typing import Tuple, Optional

class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    async def create_atomic_booking(self, db: AsyncSession, truck_id: uuid.UUID, load_id: uuid.UUID) -> Tuple[Optional[Booking], Optional[str]]:
        # Begin transaction implicitly handled by db session, but we use with_for_update
        truck_stmt = select(Truck).where(Truck.id == truck_id).with_for_update()
        load_stmt = select(Load).where(Load.id == load_id).with_for_update()
        
        truck_res = await db.execute(truck_stmt)
        truck = truck_res.scalars().first()
        
        load_res = await db.execute(load_stmt)
        load = load_res.scalars().first()
        
        if not truck or not load:
            await db.rollback()
            return None, "Invalid Truck or Load."
            
        if truck.status != "open" or load.status != "open":
            await db.rollback()
            return None, "Truck or Load is no longer available."
            
        booking = Booking(
            truck_id=truck.id,
            load_id=load.id,
            price=0.0,
            status="INITIATED",
            payment_status="PENDING",
            payment_link=None,
            payment_reference_id=None
        )
        truck.status = "RESERVED"
        load.status = "RESERVED"
        
        db.add(booking)
        db.add(truck)
        db.add(load)
        
        await db.commit()
        await db.refresh(booking)
        
        return booking, None

booking_service = CRUDBooking(Booking)
