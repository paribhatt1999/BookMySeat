from datetime import datetime,timedelta
from sqlalchemy import delete,select
from sqlalchemy.orm import Session
from .models import Booking,BookingSeat,Seat,SeatReservation

def release_expired(db:Session):
    db.execute(delete(SeatReservation).where(SeatReservation.reservation_expiry<=datetime.utcnow()))
    db.commit()

def reserve(db:Session,user_id:int,showtime_id:int,seat_ids:list[int]):
    release_expired(db)
    now=datetime.utcnow()
    seats=db.scalars(select(Seat).where(Seat.showtime_id==showtime_id,Seat.seat_id.in_(seat_ids)).with_for_update()).all()
    if len(seats)!=len(set(seat_ids)): raise ValueError("Invalid seat selection")
    for seat in seats:
        if seat.is_booked: raise ValueError(f"Seat {seat.seat_number} is already booked")
        held=db.scalar(select(SeatReservation).where(SeatReservation.showtime_id==showtime_id,SeatReservation.seat_id==seat.seat_id,SeatReservation.reservation_expiry>now).with_for_update())
        if held and held.user_id!=user_id: raise ValueError(f"Seat {seat.seat_number} is temporarily held")
    db.execute(delete(SeatReservation).where(SeatReservation.user_id==user_id,SeatReservation.showtime_id==showtime_id))
    first=None
    for seat in seats:
        r=SeatReservation(user_id=user_id,showtime_id=showtime_id,seat_id=seat.seat_id,reservation_expiry=now+timedelta(minutes=5))
        db.add(r); first=first or r
    db.commit(); db.refresh(first)
    return first

def confirm_booking(db:Session,user_id:int,showtime_id:int,reservation_id:int):
    now=datetime.utcnow()
    anchor=db.scalar(select(SeatReservation).where(SeatReservation.reservation_id==reservation_id,SeatReservation.user_id==user_id,SeatReservation.showtime_id==showtime_id,SeatReservation.reservation_expiry>now).with_for_update())
    if not anchor: raise ValueError("Reservation expired or not found")
    holds=db.scalars(select(SeatReservation).where(SeatReservation.user_id==user_id,SeatReservation.showtime_id==showtime_id,SeatReservation.reservation_expiry>now).with_for_update()).all()
    seats=db.scalars(select(Seat).where(Seat.seat_id.in_([h.seat_id for h in holds])).with_for_update()).all()
    if any(s.is_booked for s in seats): raise ValueError("A selected seat has become unavailable")
    total=sum(s.price for s in seats)
    booking=Booking(user_id=user_id,showtime_id=showtime_id,total_price=total,booking_status="confirmed",booking_time=now,payment_expiry=now)
    db.add(booking); db.flush()
    for seat in seats:
        seat.is_booked=True; seat.booked_by=user_id
        db.add(BookingSeat(booking_id=booking.booking_id,seat_id=seat.seat_id))
    db.execute(delete(SeatReservation).where(SeatReservation.reservation_id.in_([h.reservation_id for h in holds])))
    db.commit(); db.refresh(booking); return booking
