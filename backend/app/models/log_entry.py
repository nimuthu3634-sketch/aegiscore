from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IdMixin
from app.utils.time import utc_now


class LogEntry(Base, IdMixin):
    __tablename__ = "log_entries"

    source: Mapped[str] = mapped_column(String(120), nullable=False)
    source_tool: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_log: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_log: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
