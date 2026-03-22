from datetime import datetime

from pydantic import BaseModel

from app.core.enums import ResponseActionMode, ResponseActionStatus, ResponseActionType
from app.schemas.base import ORMModel


class ResponseActionSuggestion(BaseModel):
    action_type: ResponseActionType
    label: str
    description: str
    target_label: str | None = None
    available: bool
    automated: bool = False


class ResponseActionRead(ORMModel):
    id: str
    alert_id: str
    action_type: ResponseActionType
    status: ResponseActionStatus
    execution_mode: ResponseActionMode
    target_label: str | None = None
    notes: str
    result_summary: str
    performed_by_user_id: str | None = None
    performed_by_name: str
    incident_id: str | None = None
    created_at: datetime


class AlertResponseActionsResponse(BaseModel):
    items: list[ResponseActionRead]
    recommended_actions: list[ResponseActionSuggestion]


class ResponseActionExecuteRequest(BaseModel):
    action_type: ResponseActionType
    notes: str = ""
