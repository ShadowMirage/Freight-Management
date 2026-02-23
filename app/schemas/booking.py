import uuid
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


from app.models.enums import BookingStatus, PaymentStatus

class BookingBase(BaseModel):
    truck_id: uuid.UUID
    load_id: uuid.UUID
    price: float
    status: str = BookingStatus.INITIATED
    payment_status: str = PaymentStatus.PAYMENT_PENDING
    payment_link: Optional[str] = None
    payment_reference_id: Optional[str] = None
    booking_reference_id: Optional[str] = None
    payment_expires_at: Optional[datetime] = None


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    status: Optional[str] = None


class BookingResponse(BookingBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
