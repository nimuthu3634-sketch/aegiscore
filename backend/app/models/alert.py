from sqlalchemy import Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import AlertSeverity, AlertStatus
from app.db.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class Alert(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "alerts"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    source_tool: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity), nullable=False)
    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), default=AlertStatus.NEW, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
