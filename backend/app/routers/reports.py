from fastapi import APIRouter

from app.schemas.reports import ReportSummary
from app.services.reports import get_reports_summary

router = APIRouter()


@router.get("/summary", response_model=ReportSummary)
def reports_summary() -> ReportSummary:
    return ReportSummary.model_validate(get_reports_summary())
