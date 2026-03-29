from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_optional_ip, require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.models.entities import AuditLog, JobRecord, User, UserRole
from app.schemas.domain import AuditLogRead, JobRead, UserCreate, UserRead, UserUpdate
from app.services.audit import record_audit

router = APIRouter()


@router.get("/users")
def list_users(
    _: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    items = db.query(User).order_by(User.created_at.desc()).all()
    return {"items": [UserRead.model_validate(item).model_dump() for item in items], "total": len(items)}


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> UserRead:
    existing = db.query(User).filter(User.email == payload.email).one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with that email already exists")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    record_audit(
        db,
        actor=current_user,
        action="user.created",
        entity_type="user",
        entity_id=user.id,
        details={"email": user.email, "role": user.role},
        ip_address=ip_address,
    )
    return UserRead.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: str,
    payload: UserUpdate,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> UserRead:
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    record_audit(
        db,
        actor=current_user,
        action="user.updated",
        entity_type="user",
        entity_id=user.id,
        details=payload.model_dump(exclude_none=True, exclude={"password"}),
        ip_address=ip_address,
    )
    return UserRead.model_validate(user)


@router.get("/audit-logs")
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    _: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    items = db.query(AuditLog).options(joinedload(AuditLog.actor)).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {"items": [AuditLogRead.model_validate(item).model_dump() for item in items], "total": len(items)}


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: str, _: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)) -> JobRead:
    record = db.query(JobRecord).filter(JobRecord.id == job_id).one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobRead.model_validate(record)
