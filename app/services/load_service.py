from typing import Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.load import Load
from app.schemas.load import LoadCreate, LoadUpdate
from app.services.base import CRUDBase

class CRUDLoad(CRUDBase[Load, LoadCreate, LoadUpdate]):
    async def create_with_matches(self, db: AsyncSession, *, obj_in: LoadCreate) -> Tuple[Load, List]:
        from app.matching.engine import matching_engine
        load = await super().create(db=db, obj_in=obj_in)
        matches = await matching_engine.find_trucks_for_load(db, load=load)
        return load, matches

load_service = CRUDLoad(Load)
