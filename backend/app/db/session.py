from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


def _engine_connect_args() -> dict:
    if settings.database_url.startswith("postgresql"):
        return {"connect_timeout": 3}

    return {}


engine = create_engine(
    settings.database_url,
    future=True,
    pool_pre_ping=True,
    connect_args=_engine_connect_args(),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
