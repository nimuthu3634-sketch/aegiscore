from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ResponseActionMode, ResponseActionStatus, ResponseActionType
from app.db.base import Base
from app.models.mixins import IdMixin
from app.utils.time import utc_now


class ResponseAction(Base, IdMixin):
    __tablename__ = "response_actions"

    alert_id: Mapped[str] = mapped_column(ForeignKey("alerts.id"), nullable=False, index=True)
    action_type: Mapped[ResponseActionType] = mapped_column(Enum(ResponseActionType), nullable=False)
    status: Mapped[ResponseActionStatus] = mapped_column(Enum(ResponseActionStatus), nullable=False)
    execution_mode: Mapped[ResponseActionMode] = mapped_column(Enum(ResponseActionMode), nullable=False)
    target_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    result_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    performed_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    incident_id: Mapped[str | None] = mapped_column(ForeignKey("incidents.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
