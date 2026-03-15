from fastapi import APIRouter, Depends, status

from app.core.enums import UserRole
from app.schemas.logs import LogEntryRead, LogIngestRequest, LogListResponse
from app.services.logs import get_log_by_id, ingest_log, list_logs
from app.utils.auth import get_current_active_user, require_roles

router = APIRouter()


@router.post("/ingest", response_model=LogEntryRead, status_code=status.HTTP_201_CREATED)
def ingest_log_entry(
    payload: LogIngestRequest,
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> LogEntryRead:
    return LogEntryRead.model_validate(ingest_log(payload.model_dump()))


@router.get("", response_model=LogListResponse)
def get_logs(current_user: dict = Depends(get_current_active_user)) -> LogListResponse:
    result = list_logs()
    return LogListResponse.model_validate(
        {
            **result,
            "items": [LogEntryRead.model_validate(log_entry) for log_entry in result["items"]],
        }
    )


@router.get("/{id}", response_model=LogEntryRead)
def get_log(id: str, current_user: dict = Depends(get_current_active_user)) -> LogEntryRead:
    return LogEntryRead.model_validate(get_log_by_id(id))
