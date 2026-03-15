from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ReportStatus, ReportType
from app.db.base import Base
from app.models.mixins import IdMixin
from app.utils.time import utc_now


class Report(Base, IdMixin):
    __tablename__ = "reports"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), default=ReportType.OPERATIONS, nullable=False)
    generated_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    content_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.DRAFT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
