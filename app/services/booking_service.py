from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingUpdate
from app.services.base import CRUDBase

class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    pass

booking_service = CRUDBooking(Booking)
