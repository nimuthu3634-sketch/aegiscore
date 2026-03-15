from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import AlertSeverity, IncidentStatus
from app.db.base import Base
from app.models.mixins import IdMixin
from app.utils.time import utc_now


class Incident(Base, IdMixin):
    __tablename__ = "incidents"

    alert_id: Mapped[str | None] = mapped_column(ForeignKey("alerts.id"), nullable=True)
    assigned_to_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    priority: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity), nullable=False)
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False
    )
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
