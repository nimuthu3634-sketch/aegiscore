from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IdMixin
from app.utils.time import utc_now


class LogEntry(Base, IdMixin):
    __tablename__ = "log_entries"

    source: Mapped[str] = mapped_column(String(120), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_message: Mapped[str] = mapped_column(Text, nullable=False)
    event_time: Mapped[object] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
