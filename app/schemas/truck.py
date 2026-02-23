import uuid
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class TruckBase(BaseModel):
    driver_id: uuid.UUID
    source_city: str
    destination_city: str
    source_lat: float
    source_lng: float
    dest_lat: float
    dest_lng: float
    departure_time: datetime
    capacity_total: float
    capacity_available: float
    status: str = "open"


class TruckCreate(TruckBase):
    pass


class TruckUpdate(BaseModel):
    status: Optional[str] = None
    capacity_available: Optional[float] = None
    departure_time: Optional[datetime] = None


class TruckResponse(TruckBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
