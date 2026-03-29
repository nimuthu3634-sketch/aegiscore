from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.domain import HealthResponse
from app.services.health import build_health_response

router = APIRouter()


@router.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health", response_model=HealthResponse)
def healthcheck(db: Session = Depends(get_db)) -> HealthResponse:
    return build_health_response(db)


@router.get("/health/ready", response_model=HealthResponse)
def readiness(db: Session = Depends(get_db)) -> HealthResponse:
    response = build_health_response(db)
    if response.database.status != "ok" or response.redis.status != "ok":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response.model_dump())
    return response
