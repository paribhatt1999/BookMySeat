from datetime import datetime
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class User(Base):
    __tablename__="users"
    user_id: Mapped[int]=mapped_column(primary_key=True)
    email: Mapped[str|None]=mapped_column(String(255), unique=True)
    phone_number: Mapped[str|None]=mapped_column(String(32), unique=True)
    firebase_uid: Mapped[str|None]=mapped_column(String(128), unique=True)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Movie(Base):
    __tablename__="movies"
    movie_id: Mapped[int]=mapped_column(primary_key=True)
    title: Mapped[str]=mapped_column(String(200), index=True)
    genre: Mapped[str]=mapped_column(String(200))
    rating: Mapped[float]=mapped_column(Numeric(3,1), default=0)
    description: Mapped[str]=mapped_column(Text)
    cast: Mapped[str]=mapped_column(Text, default="")
    duration: Mapped[int]=mapped_column(Integer)
    language: Mapped[str]=mapped_column(String(80))
    poster_url: Mapped[str]=mapped_column(Text)
    release_date: Mapped[object|None]=mapped_column(Date)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

class Theatre(Base):
    __tablename__="theatres"
    theatre_id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(200))
    location: Mapped[str]=mapped_column(String(300))
    latitude: Mapped[float]=mapped_column()
    longitude: Mapped[float]=mapped_column()
    city: Mapped[str]=mapped_column(String(100), index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

class Showtime(Base):
    __tablename__="showtimes"
    showtime_id: Mapped[int]=mapped_column(primary_key=True)
    movie_id: Mapped[int]=mapped_column(ForeignKey("movies.movie_id", ondelete="CASCADE"))
    theatre_id: Mapped[int]=mapped_column(ForeignKey("theatres.theatre_id", ondelete="CASCADE"))
    date: Mapped[object]=mapped_column(Date)
    time: Mapped[str]=mapped_column(String(10))
    format: Mapped[str]=mapped_column(String(20))
    language: Mapped[str]=mapped_column(String(80))
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

class Seat(Base):
    __tablename__="seats"
    seat_id: Mapped[int]=mapped_column(primary_key=True)
    showtime_id: Mapped[int]=mapped_column(ForeignKey("showtimes.showtime_id", ondelete="CASCADE"))
    seat_number: Mapped[str]=mapped_column(String(10))
    row_letter: Mapped[str]=mapped_column(String(2))
    seat_type: Mapped[str]=mapped_column(String(20))
    price: Mapped[float]=mapped_column(Numeric(8,2))
    is_booked: Mapped[bool]=mapped_column(Boolean, default=False)
    booked_by: Mapped[int|None]=mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"))
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
    __table_args__=(UniqueConstraint("showtime_id","seat_number"),)

class Booking(Base):
    __tablename__="bookings"
    booking_id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.user_id"))
    showtime_id: Mapped[int]=mapped_column(ForeignKey("showtimes.showtime_id"))
    total_price: Mapped[float]=mapped_column(Numeric(10,2))
    booking_status: Mapped[str]=mapped_column(String(20), default="pending")
    booking_time: Mapped[datetime|None]=mapped_column(DateTime)
    payment_expiry: Mapped[datetime|None]=mapped_column(DateTime)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

class BookingSeat(Base):
    __tablename__="booking_seats"
    booking_id: Mapped[int]=mapped_column(ForeignKey("bookings.booking_id",ondelete="CASCADE"),primary_key=True)
    seat_id: Mapped[int]=mapped_column(ForeignKey("seats.seat_id",ondelete="CASCADE"),primary_key=True)

class SeatReservation(Base):
    __tablename__="seat_reservations"
    reservation_id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.user_id"))
    showtime_id: Mapped[int]=mapped_column(ForeignKey("showtimes.showtime_id",ondelete="CASCADE"))
    seat_id: Mapped[int]=mapped_column(ForeignKey("seats.seat_id",ondelete="CASCADE"))
    reservation_expiry: Mapped[datetime]=mapped_column(DateTime,index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    __table_args__=(UniqueConstraint("showtime_id","seat_id"),)
