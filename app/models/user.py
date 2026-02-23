import uuid
from sqlalchemy import String, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import enum
from datetime import datetime


class UserRole(str, enum.Enum):
    DRIVER = "driver"
    SHIPPER = "shipper"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    rating: Mapped[float] = mapped_column(default=5.0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
