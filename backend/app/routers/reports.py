from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.db.session import get_db
from app.schemas.reports import ReportGenerateRequest, ReportRead, ReportSummary
from app.services.reports import generate_report, get_reports_summary, list_reports
from app.utils.auth import get_current_active_user, require_roles

router = APIRouter()


@router.get("", response_model=list[ReportRead])
def get_report_list(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
) -> list[ReportRead]:
    reports = list_reports(date_from=date_from, date_to=date_to, db=db)
    return [ReportRead.model_validate(report) for report in reports]


@router.get("/summary", response_model=ReportSummary)
def reports_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
) -> ReportSummary:
    return ReportSummary.model_validate(
        get_reports_summary(date_from=date_from, date_to=date_to, db=db)
    )


@router.post("/generate", response_model=ReportRead)
def generate_new_report(
    payload: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> ReportRead:
    report = generate_report(
        title=payload.title,
        report_type=payload.report_type,
        date_from=payload.date_from,
        date_to=payload.date_to,
        current_user=current_user,
        db=db,
    )
    return ReportRead.model_validate(report)
