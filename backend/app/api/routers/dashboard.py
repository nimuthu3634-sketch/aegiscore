from fastapi import APIRouter

from app.schemas.dashboard import DashboardSummary
from app.services.dashboard import get_dashboard_summary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary() -> DashboardSummary:
    return DashboardSummary.model_validate(get_dashboard_summary())
