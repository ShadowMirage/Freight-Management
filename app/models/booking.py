import uuid
from sqlalchemy import Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    truck_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trucks.id"), index=True
    )

    load_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loads.id"), index=True
    )

    price: Mapped[float]
    status: Mapped[str] = mapped_column(default="confirmed")

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    truck = relationship("Truck")
    load = relationship("Load")
