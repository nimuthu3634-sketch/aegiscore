from fastapi import APIRouter, Depends

from app.schemas.reports import ReportSummary
from app.services.reports import get_reports_summary
from app.utils.auth import get_current_active_user

router = APIRouter()


@router.get("/summary", response_model=ReportSummary)
def reports_summary(current_user: dict = Depends(get_current_active_user)) -> ReportSummary:
    return ReportSummary.model_validate(get_reports_summary())
