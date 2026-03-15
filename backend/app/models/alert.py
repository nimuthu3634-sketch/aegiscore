from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import AlertSeverity, AlertStatus
from app.db.base import Base
from app.models.mixins import IdMixin, TimestampMixin
from app.utils.time import utc_now


class Alert(Base, IdMixin, TimestampMixin):
    __tablename__ = "alerts"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity), nullable=False)
    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), default=AlertStatus.NEW, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
