from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool
from .config import settings

# Vercel/Supabase may provide DATABASE_URL without an explicit driver.
# Force SQLAlchemy to use the installed psycopg (v3), never psycopg2.
database_url = settings.database_url.strip()
if database_url.startswith("postgres://"):
    database_url = "postgresql+psycopg://" + database_url[len("postgres://"):]
elif database_url.startswith("postgresql://"):
    database_url = "postgresql+psycopg://" + database_url[len("postgresql://"):]

# Supabase transaction pooler (port 6543) does not support prepared
# statements. NullPool + prepare_threshold=None is safe for serverless.
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    poolclass=NullPool,
    connect_args={"prepare_threshold": None},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
