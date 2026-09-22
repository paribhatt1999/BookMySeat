from fastapi import Depends,FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .db import Base,engine,get_db
from .models import Booking,Movie,Seat,SeatReservation,Showtime,Theatre,User
from .schemas import BookingRequest,CancelRequest,ReservationRequest,UserUpsert
from .services import confirm_booking,release_expired,reserve

app=FastAPI(title="BookTheSeat.com API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",")],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
Base.metadata.create_all(bind=engine)

@app.get("/health")
def health(): return {"status":"ok"}

@app.post("/auth/signup")
def signup(payload:UserUpsert,db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.firebase_uid==payload.firebase_uid))
    if not user: user=User(firebase_uid=payload.firebase_uid,email=payload.email,phone_number=payload.phone_number); db.add(user)
    else: user.email,user.phone_number=payload.email,payload.phone_number
    db.commit(); db.refresh(user); return {"user_id":user.user_id,"firebase_uid":user.firebase_uid}

@app.post("/auth/login")
def login(payload:UserUpsert,db:Session=Depends(get_db)): return signup(payload,db)

@app.get("/movies")
def movies(genre:str|None=None,search:str|None=None,db:Session=Depends(get_db)):
    stmt=select(Movie)
    if genre and genre.lower()!="all": stmt=stmt.where(Movie.genre.ilike(f"%{genre}%"))
    if search: stmt=stmt.where(Movie.title.ilike(f"%{search}%"))
    return db.scalars(stmt.order_by(Movie.rating.desc())).all()

@app.get("/movies/{movie_id}")
def movie(movie_id:int,db:Session=Depends(get_db)):
    item=db.get(Movie,movie_id)
    if not item: raise HTTPException(404,"Movie not found")
    return item

@app.get("/theatres")
def theatres(city:str="Jaipur",db:Session=Depends(get_db)):
    return db.scalars(select(Theatre).where(Theatre.city.ilike(city)).order_by(Theatre.name)).all()

@app.get("/showtimes/{movie_id}/{theatre_id}/{date}")
def showtimes(movie_id:int,theatre_id:int,date:str,db:Session=Depends(get_db)):
    return db.scalars(select(Showtime).where(Showtime.movie_id==movie_id,Showtime.theatre_id==theatre_id,Showtime.date==date).order_by(Showtime.time)).all()

@app.get("/seats/{showtime_id}")
def seats(showtime_id:int,db:Session=Depends(get_db)):
    release_expired(db)
    rows=db.scalars(select(Seat).where(Seat.showtime_id==showtime_id).order_by(Seat.row_letter,Seat.seat_number)).all()
    held={r.seat_id for r in db.scalars(select(SeatReservation).where(SeatReservation.showtime_id==showtime_id,SeatReservation.reservation_expiry>__import__("datetime").datetime.utcnow())).all()}
    return [{"seat_id":s.seat_id,"seat_number":s.seat_number,"row_letter":s.row_letter,"seat_type":s.seat_type,"price":float(s.price),"is_booked":s.is_booked or s.seat_id in held} for s in rows]

@app.post("/reserve-seats")
def reserve_seats(payload:ReservationRequest,db:Session=Depends(get_db)):
    try:
        r=reserve(db,payload.user_id,payload.showtime_id,payload.seat_ids)
        return {"reservation_id":r.reservation_id,"expires_at":r.reservation_expiry}
    except ValueError as e:
        db.rollback(); raise HTTPException(409,str(e))

@app.post("/book-tickets")
def book_tickets(payload:BookingRequest,db:Session=Depends(get_db)):
    try:
        b=confirm_booking(db,payload.user_id,payload.showtime_id,payload.reservation_id)
        return {"booking_id":b.booking_id,"total_price":float(b.total_price),"status":b.booking_status}
    except ValueError as e:
        db.rollback(); raise HTTPException(409,str(e))

@app.post("/cancel-booking")
def cancel_booking(payload:CancelRequest,db:Session=Depends(get_db)):
    b=db.scalar(select(Booking).where(Booking.booking_id==payload.booking_id,Booking.user_id==payload.user_id).with_for_update())
    if not b: raise HTTPException(404,"Booking not found")
    b.booking_status="cancelled"; db.commit(); return {"status":"cancelled"}

@app.get("/booking/{booking_id}")
def booking(booking_id:int,db:Session=Depends(get_db)):
    b=db.get(Booking,booking_id)
    if not b: raise HTTPException(404,"Booking not found")
    return b
