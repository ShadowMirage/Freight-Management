from typing import Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.truck import Truck
from app.schemas.truck import TruckCreate, TruckUpdate
from app.services.base import CRUDBase

class CRUDTruck(CRUDBase[Truck, TruckCreate, TruckUpdate]):
    async def create_with_matches(self, db: AsyncSession, *, obj_in: TruckCreate) -> Tuple[Truck, List]:
        from app.matching.engine import matching_engine
        truck = await super().create(db=db, obj_in=obj_in)
        matches = await matching_engine.find_loads_for_truck(db, truck=truck)
        return truck, matches

truck_service = CRUDTruck(Truck)
