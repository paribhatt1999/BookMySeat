# BookTheSeat.com

Modern movie seat booking application built with HTML/CSS/JavaScript, FastAPI, PostgreSQL on Supabase, and Firebase Authentication.

## Stack
- Frontend: HTML5, CSS3, JavaScript ES6+
- Backend: Python FastAPI + SQLAlchemy
- Database: Supabase PostgreSQL
- Authentication: Firebase Google + Phone OTP
- Booking: 5-minute seat reservations with database constraints/row locking
- QR: booking confirmation QR

## Supabase setup

The BookMySeat Supabase project is connected to this repository.

1. Open Supabase Dashboard and get the database password from Project Settings -> Database.
2. Copy .env.example to .env.
3. Replace <SUPABASE_DB_PASSWORD> in DATABASE_URL.
4. Never put a Supabase secret/service-role key in the frontend or Git.
5. The Supabase database schema and RLS are already created. database/schema.sql is the version-controlled schema reference.
6. Sample Jaipur movies, theatres, showtimes, and seats are seeded in the connected database.

## Run locally

pip install -r backend/requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload

Serve frontend/ using VS Code Live Server on port 5500.

API docs: http://localhost:8000/docs

## Security note

Firebase authentication is currently used by the browser and synchronized to the FastAPI users table. The next production-hardening step is to verify Firebase ID tokens in FastAPI instead of trusting a client-supplied Firebase UID.

Never commit .env, Supabase database passwords, Supabase secret/service-role keys, or Firebase Admin private keys.
