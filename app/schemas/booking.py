import uuid
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class BookingBase(BaseModel):
    truck_id: uuid.UUID
    load_id: uuid.UUID
    price: float
    status: str = "confirmed"


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    status: Optional[str] = None


class BookingResponse(BookingBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
