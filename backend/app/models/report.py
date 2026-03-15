from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ReportStatus
from app.db.base import Base
from app.models.mixins import IdMixin, TimestampMixin
from app.utils.time import utc_now


class Report(Base, IdMixin, TimestampMixin):
    __tablename__ = "reports"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(120), nullable=False)
    generated_by: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), default=ReportStatus.DRAFT, nullable=False
    )
    generated_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
