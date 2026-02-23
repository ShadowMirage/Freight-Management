from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import booking_service

router = APIRouter()

@router.post("/", response_model=BookingResponse)
async def create_booking(
    *, 
    db: AsyncSession = Depends(get_db), 
    booking_in: BookingCreate
) -> Any:
    return await booking_service.create(db=db, obj_in=booking_in)

@router.get("/{booking_id}", response_model=BookingResponse)
async def read_booking(
    *, 
    db: AsyncSession = Depends(get_db), 
    booking_id: uuid.UUID
) -> Any:
    booking = await booking_service.get(db=db, id=booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@router.get("/", response_model=List[BookingResponse])
async def read_bookings(
    db: AsyncSession = Depends(get_db), 
    skip: int = 0, 
    limit: int = 100
) -> Any:
    return await booking_service.get_multi(db=db, skip=skip, limit=limit)
