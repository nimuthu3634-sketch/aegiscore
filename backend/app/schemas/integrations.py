from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.core.enums import AlertSeverity, IntegrationHealth, IntegrationTool
from app.schemas.base import ORMModel


class IntegrationRead(ORMModel):
    id: str
    tool_name: IntegrationTool
    status: IntegrationHealth
    last_sync_at: datetime
    notes: str
    imported_alert_count: int = 0
    imported_log_count: int = 0
    last_import_at: datetime | None = None
    last_import_message: str | None = None


class WazuhImportRequest(BaseModel):
    alerts: list[dict[str, Any]]


class WazuhImportResponse(BaseModel):
    imported_alert_count: int
    imported_log_count: int
    skipped_count: int
    last_import_at: datetime
    message: str


class WazuhStatusResponse(IntegrationRead):
    available_demo_payloads: int
    latest_imported_alert_titles: list[str]


class WazuhSampleAlertRead(BaseModel):
    timestamp: str
    agent: dict[str, Any]
    rule: dict[str, Any]
    full_log: str
    id: str | None = None
