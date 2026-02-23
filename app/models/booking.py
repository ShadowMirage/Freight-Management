import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base
from app.models.enums import BookingStatus, PaymentStatus


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
    status: Mapped[str] = mapped_column(default=BookingStatus.INITIATED)
    payment_status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.PAYMENT_PENDING)
    payment_link: Mapped[str] = mapped_column(String(255), nullable=True)
    payment_reference_id: Mapped[str] = mapped_column(String(100), nullable=True)
    
    booking_reference_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=True)
    payment_expires_at: Mapped[datetime] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    truck = relationship("Truck")
    load = relationship("Load")
