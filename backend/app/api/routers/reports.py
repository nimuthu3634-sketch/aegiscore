from fastapi import APIRouter

from app.schemas.reports import ReportRead
from app.services.reports import list_reports

router = APIRouter()


@router.get("", response_model=list[ReportRead])
def get_reports() -> list[ReportRead]:
    return [ReportRead.model_validate(report) for report in list_reports()]
