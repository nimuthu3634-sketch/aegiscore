from fastapi import APIRouter, Depends

from app.schemas.alerts import AlertRead
from app.services.alerts import get_alert_by_id, list_alerts
from app.utils.auth import get_current_active_user

router = APIRouter()


@router.get("", response_model=list[AlertRead])
def get_alerts(current_user: dict = Depends(get_current_active_user)) -> list[AlertRead]:
    return [AlertRead.model_validate(alert) for alert in list_alerts()]


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert(alert_id: str, current_user: dict = Depends(get_current_active_user)) -> AlertRead:
    return AlertRead.model_validate(get_alert_by_id(alert_id))
