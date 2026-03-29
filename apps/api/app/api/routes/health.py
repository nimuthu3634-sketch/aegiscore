from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def readiness() -> dict[str, str]:
    return {"status": "ready"}
