from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.core.enums import ReportStatus, ReportType
from app.schemas.base import ORMModel


class ReportRead(ORMModel):
    id: str
    title: str
    report_type: ReportType
    generated_by_user_id: str | None
    content_json: dict[str, Any]
    status: ReportStatus
    created_at: datetime


class ReportSummary(BaseModel):
    reports_generated: int
    draft_reports: int
    ready_reports: int
