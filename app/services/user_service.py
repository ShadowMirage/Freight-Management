from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.base import CRUDBase

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    pass

user_service = CRUDUser(User)
