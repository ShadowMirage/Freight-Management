import uuid
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base


class Truck(Base):
    __tablename__ = "trucks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )

    source_city: Mapped[str] = mapped_column(String, index=True)
    destination_city: Mapped[str] = mapped_column(String, index=True)

    source_lat: Mapped[float] = mapped_column(Float)
    source_lng: Mapped[float] = mapped_column(Float)
    dest_lat: Mapped[float] = mapped_column(Float)
    dest_lng: Mapped[float] = mapped_column(Float)

    departure_time: Mapped[datetime]
    capacity_total: Mapped[float]
    capacity_available: Mapped[float]

    status: Mapped[str] = mapped_column(default="open", index=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    driver = relationship("User")
