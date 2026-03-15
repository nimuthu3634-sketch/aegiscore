from datetime import datetime

from app.core.enums import ReportStatus
from app.schemas.base import ORMModel


class ReportRead(ORMModel):
    id: str
    name: str
    report_type: str
    generated_by: str
    status: ReportStatus
    generated_at: datetime
