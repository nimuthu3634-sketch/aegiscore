from typing import Any

from sqlalchemy import JSON, Boolean, Enum, Float, String, Text
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
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_anomalous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anomaly_explanation: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    integration_ref: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    finding_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    parser_status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lab_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
