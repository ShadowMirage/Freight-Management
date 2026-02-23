from pydantic import BaseModel, Field, field_validator
import datetime

class PickupDropCityValidator(BaseModel):
    city: str = Field(..., min_length=3)

class CapacityValidator(BaseModel):
    capacity: int = Field(..., ge=1, le=100)

class DateValidator(BaseModel):
    date_str: str

    @field_validator('date_str')
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            dt = datetime.datetime.strptime(v, "%d-%m-%Y").date()
            if dt < datetime.date.today():
                raise ValueError("Date cannot be in the past")
            return v
        except ValueError as e:
            if "does not match format" in str(e):
                raise ValueError("Invalid format. Use DD-MM-YYYY")
            raise e
