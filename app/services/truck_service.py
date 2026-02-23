from app.models.truck import Truck
from app.schemas.truck import TruckCreate, TruckUpdate
from app.services.base import CRUDBase

class CRUDTruck(CRUDBase[Truck, TruckCreate, TruckUpdate]):
    pass

truck_service = CRUDTruck(Truck)
