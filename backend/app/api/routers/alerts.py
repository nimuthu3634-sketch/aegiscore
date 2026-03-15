from fastapi import APIRouter

from app.schemas.alerts import AlertRead
from app.services.alerts import list_alerts

router = APIRouter()


@router.get("", response_model=list[AlertRead])
def get_alerts() -> list[AlertRead]:
    return [AlertRead.model_validate(alert) for alert in list_alerts()]
