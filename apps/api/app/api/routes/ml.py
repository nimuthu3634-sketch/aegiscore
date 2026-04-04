from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_ip, require_roles
from app.db.session import get_db
from app.models.entities import ModelMetadata, User, UserRole
from app.ml.scoring import build_risk_overview
from app.schemas.domain import (
    RetrainResponse,
    RiskModelMetadataListResponse,
    RiskModelMetadataRead,
    RiskOverviewRead,
    ScoreRecalculationRequest,
    ScoreRecalculationResponse,
)
from app.services.audit import record_audit
from app.services.domain import rescore_alerts
from app.services.jobs import enqueue_model_retrain

router = APIRouter()


@router.get("/model", response_model=RiskModelMetadataRead)
def get_model(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> RiskModelMetadataRead:
    _ = current_user
    model = db.query(ModelMetadata).filter(ModelMetadata.is_active.is_(True)).order_by(ModelMetadata.trained_at.desc()).first()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trained model metadata found")
    return RiskModelMetadataRead.model_validate(model)


@router.get("/models", response_model=RiskModelMetadataListResponse)
def list_models(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RiskModelMetadataListResponse:
    query = db.query(ModelMetadata)
    total = query.count()
    items = query.order_by(ModelMetadata.trained_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return RiskModelMetadataListResponse(
        items=[RiskModelMetadataRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/overview", response_model=RiskOverviewRead)
def get_risk_overview(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RiskOverviewRead:
    overview = build_risk_overview(db)
    active_model = overview.pop("active_model", None)
    return RiskOverviewRead(
        active_model=RiskModelMetadataRead.model_validate(active_model) if active_model is not None else None,
        **overview,
    )


@router.post("/retrain", response_model=RetrainResponse, status_code=status.HTTP_202_ACCEPTED)
def retrain(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> RetrainResponse:
    record = enqueue_model_retrain(db, current_user)
    return RetrainResponse(job_id=record.id, status=record.status)


@router.post("/recalculate", response_model=ScoreRecalculationResponse)
def recalculate_scores(
    payload: ScoreRecalculationRequest | None = None,
    ip_address: str | None = Depends(get_optional_ip),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> ScoreRecalculationResponse:
    payload = payload or ScoreRecalculationRequest()
    result = rescore_alerts(db, source=payload.source, open_only=payload.open_only, limit=payload.limit)
    record_audit(
        db,
        actor=current_user,
        action="ml.scores_recalculated",
        entity_type="risk-model",
        entity_id=None,
        details=payload.model_dump(exclude_none=True) | result,
        ip_address=ip_address,
    )
    return ScoreRecalculationResponse(**result)
