import uuid
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class LoadBase(BaseModel):
    shipper_id: uuid.UUID
    pickup_city: str
    drop_city: str
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float
    weight: float
    deadline: datetime
    status: str = "open"


class LoadCreate(LoadBase):
    pass


class LoadUpdate(BaseModel):
    status: Optional[str] = None


class LoadResponse(LoadBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
