from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.truck import TruckCreate, TruckResponse
from app.services.truck_service import truck_service

router = APIRouter()

@router.post("/", response_model=TruckResponse)
async def create_truck(
    *, 
    db: AsyncSession = Depends(get_db), 
    truck_in: TruckCreate
) -> Any:
    return await truck_service.create(db=db, obj_in=truck_in)

@router.get("/{truck_id}", response_model=TruckResponse)
async def read_truck(
    *, 
    db: AsyncSession = Depends(get_db), 
    truck_id: uuid.UUID
) -> Any:
    truck = await truck_service.get(db=db, id=truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck

@router.get("/", response_model=List[TruckResponse])
async def read_trucks(
    db: AsyncSession = Depends(get_db), 
    skip: int = 0, 
    limit: int = 100
) -> Any:
    return await truck_service.get_multi(db=db, skip=skip, limit=limit)
