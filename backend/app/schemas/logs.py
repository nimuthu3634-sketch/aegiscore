from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.core.enums import AlertSeverity
from app.schemas.base import ORMModel


class LogIngestRequest(BaseModel):
    source: str | None = None
    source_tool: str
    raw_log: dict[str, Any]
    timestamp: str | int | float | None = None
    severity: str | int | float | None = None
    event_type: str | None = None


class LogEntryRead(ORMModel):
    id: str
    source: str
    source_tool: str
    raw_log: dict[str, Any]
    normalized_log: dict[str, Any]
    event_type: str
    severity: AlertSeverity
    integration_ref: str | None = None
    parser_status: str | None = None
    lab_only: bool = False
    finding_metadata: dict[str, Any] = {}
    created_at: datetime


class LogListResponse(BaseModel):
    items: list[LogEntryRead]
    total_items: int
