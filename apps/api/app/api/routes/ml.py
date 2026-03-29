from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.entities import ModelMetadata, User, UserRole
from app.schemas.domain import ModelMetadataRead, RetrainResponse
from app.services.jobs import enqueue_model_retrain

router = APIRouter()


@router.get("/model", response_model=ModelMetadataRead)
def get_model(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ModelMetadataRead:
    _ = current_user
    model = db.query(ModelMetadata).filter(ModelMetadata.is_active.is_(True)).order_by(ModelMetadata.trained_at.desc()).first()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trained model metadata found")
    return ModelMetadataRead.model_validate(model)


@router.post("/retrain", response_model=RetrainResponse, status_code=status.HTTP_202_ACCEPTED)
def retrain(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> RetrainResponse:
    record = enqueue_model_retrain(db, current_user)
    return RetrainResponse(job_id=record.id, status=record.status)
