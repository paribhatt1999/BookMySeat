from datetime import datetime, timezone
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

import jwt
from cryptography import x509
from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .models import Booking, Movie, Seat, SeatReservation, Showtime, Theatre, User
from .schemas import BookingRequest, CancelRequest, ReservationRequest, UserUpsert
from .services import confirm_booking, release_expired, reserve

FIREBASE_CERTS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
_firebase_certs = {}
_firebase_certs_expires_at = 0.0


def _get_firebase_certs() -> dict:
    global _firebase_certs, _firebase_certs_expires_at
    now = time.time()
    if _firebase_certs and now < _firebase_certs_expires_at:
        return _firebase_certs

    request = Request(FIREBASE_CERTS_URL, headers={"User-Agent": "BookTheSeat/1.0"})
    with urlopen(request, timeout=10) as response:
        raw = response.read().decode("utf-8")
        cache_control = response.headers.get("Cache-Control", "")

    certificates = json.loads(raw)
    _firebase_certs = certificates
    max_age = 3600
    for part in cache_control.split(","):
        part = part.strip()
        if part.startswith("max-age="):
            try:
                max_age = max(60, int(part.split("=", 1)[1]))
            except ValueError:
                pass
            break
    _firebase_certs_expires_at = time.time() + max_age
    return _firebase_certs


def current_firebase_uid(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(401, "Authentication required")

    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256":
            raise HTTPException(401, "Invalid Firebase token")

        kid = header.get("kid")
        if not kid:
            raise HTTPException(401, "Invalid Firebase token")

        certificates = _get_firebase_certs()
        certificate_pem = certificates.get(kid)
        if not certificate_pem:
            _firebase_certs.clear()
            certificate_pem = _get_firebase_certs().get(kid)
        if not certificate_pem:
            raise HTTPException(401, "Invalid Firebase token")

        certificate = x509.load_pem_x509_certificate(certificate_pem.encode("utf-8"))
        decoded = jwt.decode(
            token,
            certificate.public_key(),
            algorithms=["RS256"],
            audience=settings.firebase_project_id,
            issuer=f"https://securetoken.google.com/{settings.firebase_project_id}",
            options={"require": ["exp", "iat", "sub", "auth_time"]},
        )

        if decoded["auth_time"] > int(datetime.now(timezone.utc).timestamp()):
            raise HTTPException(401, "Invalid Firebase token")

        uid = decoded.get("sub")
        if not uid:
            raise HTTPException(401, "Invalid Firebase token")
        return uid
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(401, "Invalid or expired Firebase token")


def current_user(db: Session, uid: str) -> User:
    user = db.scalar(select(User).where(User.firebase_uid == uid))
    if not user:
        raise HTTPException(401, "User profile not found")
    return user


app = FastAPI(title="BookTheSeat.com API", version="1.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/signup")
def signup(payload: UserUpsert, uid: str = Depends(current_firebase_uid), db: Session = Depends(get_db)):
    if payload.firebase_uid != uid:
        raise HTTPException(403, "Firebase UID does not match token")
    user = db.scalar(select(User).where(User.firebase_uid == uid))
    if not user:
        user = User(firebase_uid=uid, email=payload.email, phone_number=payload.phone_number)
        db.add(user)
    else:
        user.email, user.phone_number = payload.email, payload.phone_number
    db.commit()
    db.refresh(user)
    return {"user_id": user.user_id, "firebase_uid": user.firebase_uid}


@app.get("/movies")
def movies(genre: str | None = None, search: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Movie)
    if genre and genre.lower() != "all":
        stmt = stmt.where(Movie.genre.ilike(f"%{genre}%"))
    if search:
        stmt = stmt.where(Movie.title.ilike(f"%{search}%"))
    return db.scalars(stmt.order_by(Movie.rating.desc())).all()


@app.get("/movies/{movie_id}")
def movie(movie_id: int, db: Session = Depends(get_db)):
    item = db.get(Movie, movie_id)
    if not item:
        raise HTTPException(404, "Movie not found")
    return item


@app.get("/theatres")
def theatres(city: str = "Jaipur", db: Session = Depends(get_db)):
    return db.scalars(select(Theatre).where(Theatre.city.ilike(city)).order_by(Theatre.name)).all()


@app.get("/showtimes/{movie_id}/{theatre_id}/{date}")
def showtimes(movie_id: int, theatre_id: int, date: str, db: Session = Depends(get_db)):
    return db.scalars(
        select(Showtime)
        .where(
            Showtime.movie_id == movie_id,
            Showtime.theatre_id == theatre_id,
            Showtime.date == date,
        )
        .order_by(Showtime.time)
    ).all()


@app.get("/seats/{showtime_id}")
def seats(showtime_id: int, db: Session = Depends(get_db)):
    release_expired(db)
    rows = db.scalars(
        select(Seat)
        .where(Seat.showtime_id == showtime_id)
        .order_by(Seat.row_letter, Seat.seat_number)
    ).all()
    now = datetime.utcnow()
    held = {
        r.seat_id
        for r in db.scalars(
            select(SeatReservation).where(
                SeatReservation.showtime_id == showtime_id,
                SeatReservation.reservation_expiry > now,
            )
        ).all()
    }
    return [
        {
            "seat_id": s.seat_id,
            "seat_number": s.seat_number,
            "row_letter": s.row_letter,
            "seat_type": s.seat_type,
            "price": float(s.price),
            "is_booked": s.is_booked or s.seat_id in held,
        }
        for s in rows
    ]


@app.post("/reserve-seats")
def reserve_seats(payload: ReservationRequest, uid: str = Depends(current_firebase_uid), db: Session = Depends(get_db)):
    user = current_user(db, uid)
    if payload.user_id != user.user_id:
        raise HTTPException(403, "User mismatch")
    try:
        r = reserve(db, payload.user_id, payload.showtime_id, payload.seat_ids)
        return {"reservation_id": r.reservation_id, "expires_at": r.reservation_expiry}
    except ValueError as e:
        db.rollback()
        raise HTTPException(409, str(e))


@app.post("/book-tickets")
def book_tickets(payload: BookingRequest, uid: str = Depends(current_firebase_uid), db: Session = Depends(get_db)):
    user = current_user(db, uid)
    if payload.user_id != user.user_id:
        raise HTTPException(403, "User mismatch")
    try:
        b = confirm_booking(db, payload.user_id, payload.showtime_id, payload.reservation_id)
        return {
            "booking_id": b.booking_id,
            "total_price": float(b.total_price),
            "status": b.booking_status,
            "booking_time": b.booking_time,
        }
    except ValueError as e:
        db.rollback()
        raise HTTPException(409, str(e))


@app.post("/cancel-booking")
def cancel_booking(payload: CancelRequest, uid: str = Depends(current_firebase_uid), db: Session = Depends(get_db)):
    user = current_user(db, uid)
    if payload.user_id != user.user_id:
        raise HTTPException(403, "User mismatch")
    b = db.scalar(
        select(Booking)
        .where(Booking.booking_id == payload.booking_id, Booking.user_id == user.user_id)
        .with_for_update()
    )
    if not b:
        raise HTTPException(404, "Booking not found")
    b.booking_status = "cancelled"
    db.commit()
    return {"status": "cancelled"}


@app.get("/bookings/me")
def my_bookings(uid: str = Depends(current_firebase_uid), db: Session = Depends(get_db)):
    user = current_user(db, uid)
    return db.scalars(
        select(Booking)
        .where(Booking.user_id == user.user_id)
        .order_by(Booking.created_at.desc())
    ).all()


@app.get("/booking/{booking_id}")
def booking(booking_id: int, uid: str = Depends(current_firebase_uid), db: Session = Depends(get_db)):
    user = current_user(db, uid)
    b = db.scalar(
        select(Booking).where(
            Booking.booking_id == booking_id,
            Booking.user_id == user.user_id,
        )
    )
    if not b:
        raise HTTPException(404, "Booking not found")
    return b


# Keep this mount LAST so API routes above always take precedence.
# It makes the existing plain HTML/CSS/JS frontend available at the Vercel root.
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
