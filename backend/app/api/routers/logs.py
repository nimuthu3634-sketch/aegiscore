from fastapi import APIRouter

from app.schemas.logs import LogEntryRead
from app.services.logs import list_logs

router = APIRouter()


@router.get("", response_model=list[LogEntryRead])
def get_logs() -> list[LogEntryRead]:
    return [LogEntryRead.model_validate(log) for log in list_logs()]
