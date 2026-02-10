from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine_kwargs = {
    "echo": True,
    "connect_args": {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
}
if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update(
        {"pool_size": 5, "max_overflow": 10, "pool_recycle": 3600}
    )

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
