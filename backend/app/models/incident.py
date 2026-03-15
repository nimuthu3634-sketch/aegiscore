from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import AlertSeverity, IncidentStatus
from app.db.base import Base
from app.models.mixins import IdMixin, TimestampMixin


class Incident(Base, IdMixin, TimestampMixin):
    __tablename__ = "incidents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    owner_name: Mapped[str] = mapped_column(String(120), default="Unassigned", nullable=False)
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False
    )
    priority: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity), nullable=False)
