from typing import Any

from datetime import datetime

from app.schemas.base import ORMModel


class LogEntryRead(ORMModel):
    id: str
    source: str
    source_tool: str
    raw_log: str
    normalized_log: dict[str, Any]
    event_type: str
    severity: str
    created_at: datetime
