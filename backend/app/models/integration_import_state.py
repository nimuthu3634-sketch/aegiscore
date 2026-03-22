from datetime import datetime

from sqlalchemy import DateTime, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import IntegrationTool
from app.db.base import Base


class IntegrationImportState(Base):
    __tablename__ = "integration_import_states"

    tool_name: Mapped[IntegrationTool] = mapped_column(
        Enum(IntegrationTool), primary_key=True
    )
    last_import_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_import_message: Mapped[str | None] = mapped_column(Text, nullable=True)
