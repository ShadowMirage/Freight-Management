from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from app.models.truck import Truck
from app.models.load import Load

class MatchingEngine:
    @staticmethod
    async def find_loads_for_truck(db: AsyncSession, truck: Truck) -> List[Load]:
        query = select(Load).where(
            Load.pickup_city.ilike(truck.source_city),
            Load.drop_city.ilike(truck.destination_city),
            Load.weight <= truck.capacity_available,
            Load.status == "open",
            Load.deadline.between(truck.departure_time - timedelta(days=1), truck.departure_time + timedelta(days=1))
        ).limit(5)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def find_trucks_for_load(db: AsyncSession, load: Load) -> List[Truck]:
        query = select(Truck).where(
            Truck.source_city.ilike(load.pickup_city),
            Truck.destination_city.ilike(load.drop_city),
            Truck.capacity_available >= load.weight,
            Truck.status == "open",
            Truck.departure_time.between(load.deadline - timedelta(days=1), load.deadline + timedelta(days=1))
        ).limit(5)
        
        result = await db.execute(query)
        return list(result.scalars().all())

matching_engine = MatchingEngine()
