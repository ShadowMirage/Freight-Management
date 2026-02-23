from app.models.load import Load
from app.schemas.load import LoadCreate, LoadUpdate
from app.services.base import CRUDBase

class CRUDLoad(CRUDBase[Load, LoadCreate, LoadUpdate]):
    pass

load_service = CRUDLoad(Load)
