import enum

class BookingStatus(str, enum.Enum):
    INITIATED = "INITIATED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    PAID = "PAID"
    FAILED = "FAILED"

class PaymentStatus(str, enum.Enum):
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    FAILED = "FAILED"

class FreightStatus(str, enum.Enum):
    OPEN = "open" # lower case because matching engine strict matching relies on 'open'
    RESERVED = "RESERVED"
    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"
