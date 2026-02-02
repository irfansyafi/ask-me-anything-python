import os

from dotenv import load_dotenv
from pytz import timezone
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Database URL (fallback to sqlite for local development)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ama.db")

# Create engine with sqlite-specific args if needed
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Malaysia timezone used across app
malaysia_tz = timezone("Asia/Kuala_Lumpur")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
