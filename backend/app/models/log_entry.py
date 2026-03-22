from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import IdMixin
from app.utils.time import utc_now


class LogEntry(Base, IdMixin):
    __tablename__ = "log_entries"

    source: Mapped[str] = mapped_column(String(120), nullable=False)
    source_tool: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_log: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    normalized_log: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    integration_ref: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    finding_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    parser_status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lab_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
