from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4

from app.utils.time import utc_now


class IdMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))


class TimestampMixin:
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
