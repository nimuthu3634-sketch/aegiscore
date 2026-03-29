from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import User
from app.schemas.domain import DashboardSummary
from app.services.domain import build_dashboard_summary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def summary(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DashboardSummary:
    return build_dashboard_summary(db)
