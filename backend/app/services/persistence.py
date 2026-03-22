from __future__ import annotations

from collections.abc import Callable
from time import monotonic
from typing import TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.db.session import SessionLocal

T = TypeVar("T")
DB_RETRY_BACKOFF_SECONDS = 15.0
_db_unavailable_until = 0.0


def run_with_optional_db(
    operation: Callable[[Session], T],
    fallback: Callable[[], T],
) -> T:
    global _db_unavailable_until

    if monotonic() < _db_unavailable_until:
        return fallback()

    db: Session | None = None
    try:
        init_db()
        db = SessionLocal()
        result = operation(db)
        _db_unavailable_until = 0.0
        return result
    except SQLAlchemyError:
        _db_unavailable_until = monotonic() + DB_RETRY_BACKOFF_SECONDS
        if db is not None:
            db.rollback()
        return fallback()
    finally:
        if db is not None:
            db.close()
