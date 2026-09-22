from datetime import datetime
from pydantic import BaseModel, Field

class UserUpsert(BaseModel):
    email: str|None=None
    phone_number: str|None=None
    firebase_uid: str

class ReservationRequest(BaseModel):
    user_id: int
    showtime_id: int
    seat_ids: list[int]=Field(min_length=1,max_length=10)

class BookingRequest(BaseModel):
    user_id: int
    showtime_id: int
    reservation_id: int

class CancelRequest(BaseModel):
    booking_id:int
    user_id:int
