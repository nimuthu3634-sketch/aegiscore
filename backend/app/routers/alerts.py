from fastapi import APIRouter

from app.schemas.alerts import AlertRead
from app.services.alerts import get_alert_by_id, list_alerts

router = APIRouter()


@router.get("", response_model=list[AlertRead])
def get_alerts() -> list[AlertRead]:
    return [AlertRead.model_validate(alert) for alert in list_alerts()]


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert(alert_id: str) -> AlertRead:
    return AlertRead.model_validate(get_alert_by_id(alert_id))
