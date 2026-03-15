from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import IntegrationHealth, IntegrationTool
from app.db.base import Base
from app.models.mixins import IdMixin
from app.utils.time import utc_now


class IntegrationStatus(Base, IdMixin):
    __tablename__ = "integration_statuses"

    tool_name: Mapped[IntegrationTool] = mapped_column(Enum(IntegrationTool), nullable=False)
    status: Mapped[IntegrationHealth] = mapped_column(
        Enum(IntegrationHealth), default=IntegrationHealth.PENDING, nullable=False
    )
    last_sync_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
