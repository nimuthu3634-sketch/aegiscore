from fastapi import APIRouter, Depends

from app.schemas.alerts import AlertRead
from app.schemas.dashboard import DashboardCharts, DashboardRecentIncident, DashboardSummary
from app.services.dashboard import (
    get_dashboard_charts,
    get_dashboard_recent_alerts,
    get_dashboard_recent_incidents,
    get_dashboard_summary,
)
from app.utils.auth import get_current_active_user

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(current_user: dict = Depends(get_current_active_user)) -> DashboardSummary:
    return DashboardSummary.model_validate(get_dashboard_summary())


@router.get("/charts", response_model=DashboardCharts)
def dashboard_charts(current_user: dict = Depends(get_current_active_user)) -> DashboardCharts:
    return DashboardCharts.model_validate(get_dashboard_charts())


@router.get("/recent-alerts", response_model=list[AlertRead])
def dashboard_recent_alerts(current_user: dict = Depends(get_current_active_user)) -> list[AlertRead]:
    return [AlertRead.model_validate(alert) for alert in get_dashboard_recent_alerts()]


@router.get("/recent-incidents", response_model=list[DashboardRecentIncident])
def dashboard_recent_incidents(
    current_user: dict = Depends(get_current_active_user),
) -> list[DashboardRecentIncident]:
    return [
        DashboardRecentIncident.model_validate(incident)
        for incident in get_dashboard_recent_incidents()
    ]
