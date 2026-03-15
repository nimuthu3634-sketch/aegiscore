from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import IntegrationType
from app.db.base import Base
from app.models.mixins import IdMixin, TimestampMixin
from app.utils.time import utc_now


class Integration(Base, IdMixin, TimestampMixin):
    __tablename__ = "integrations"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    integration_type: Mapped[IntegrationType] = mapped_column(Enum(IntegrationType), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sync_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
