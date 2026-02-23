import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base


class Load(Base):
    __tablename__ = "loads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    shipper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )

    pickup_city: Mapped[str] = mapped_column(String, index=True)
    drop_city: Mapped[str] = mapped_column(String, index=True)

    pickup_lat: Mapped[float]
    pickup_lng: Mapped[float]
    drop_lat: Mapped[float]
    drop_lng: Mapped[float]

    weight: Mapped[float]
    category: Mapped[str] = mapped_column(String(50), default="General")
    deadline: Mapped[datetime]

    status: Mapped[str] = mapped_column(default="open", index=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    shipper = relationship("User")
