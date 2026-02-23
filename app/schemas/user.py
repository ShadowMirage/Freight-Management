import uuid
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    phone_number: str = Field(..., max_length=20)
    role: UserRole


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    phone_number: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRole] = None
    rating: Optional[float] = None


class UserResponse(UserBase):
    id: uuid.UUID
    rating: float
    created_at: datetime

    class Config:
        from_attributes = True
