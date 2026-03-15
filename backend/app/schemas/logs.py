from datetime import datetime

from app.schemas.base import ORMModel


class LogEntryRead(ORMModel):
    id: str
    source: str
    event_type: str
    severity: str
    raw_message: str
    event_time: datetime
