from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import user_service

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(
    *, 
    db: AsyncSession = Depends(get_db), 
    user_in: UserCreate
) -> Any:
    return await user_service.create(db=db, obj_in=user_in)

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    *, 
    db: AsyncSession = Depends(get_db), 
    user_id: uuid.UUID
) -> Any:
    user = await user_service.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=List[UserResponse])
async def read_users(
    db: AsyncSession = Depends(get_db), 
    skip: int = 0, 
    limit: int = 100
) -> Any:
    return await user_service.get_multi(db=db, skip=skip, limit=limit)
