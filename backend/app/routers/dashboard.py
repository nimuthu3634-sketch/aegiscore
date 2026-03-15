from fastapi import APIRouter, Depends

from app.schemas.dashboard import DashboardSummary
from app.services.dashboard import get_dashboard_summary
from app.utils.auth import get_current_active_user

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(current_user: dict = Depends(get_current_active_user)) -> DashboardSummary:
    return DashboardSummary.model_validate(get_dashboard_summary())
