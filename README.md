# BookTheSeat.com

Modern movie seat booking demo built with HTML/CSS/JavaScript, FastAPI, PostgreSQL/Supabase, and Firebase authentication hooks.

See the repository folders for the FastAPI backend, responsive frontend, Supabase schema/seed files, and environment template.

## Run
```bash
pip install -r backend/requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload
```

Serve `frontend/` using a static server such as VS Code Live Server.

API docs: `http://localhost:8000/docs`

The reservation flow uses a five-minute hold, transactional seat locking, and simulated payment. Production deployment should add Firebase Admin token verification and scheduled expiry cleanup.