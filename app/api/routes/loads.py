from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.load import LoadCreate, LoadResponse
from app.services.load_service import load_service

router = APIRouter()

@router.post("/", response_model=LoadResponse)
async def create_load(
    *, 
    db: AsyncSession = Depends(get_db), 
    load_in: LoadCreate
) -> Any:
    return await load_service.create(db=db, obj_in=load_in)

@router.get("/{load_id}", response_model=LoadResponse)
async def read_load(
    *, 
    db: AsyncSession = Depends(get_db), 
    load_id: uuid.UUID
) -> Any:
    load = await load_service.get(db=db, id=load_id)
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    return load

@router.get("/", response_model=List[LoadResponse])
async def read_loads(
    db: AsyncSession = Depends(get_db), 
    skip: int = 0, 
    limit: int = 100
) -> Any:
    return await load_service.get_multi(db=db, skip=skip, limit=limit)
