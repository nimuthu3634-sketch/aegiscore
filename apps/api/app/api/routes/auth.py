from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.entities import User
from app.schemas.domain import LoginRequest, ProfileUpdate, TokenResponse, UserRead
from app.services.audit import record_audit

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    token = create_access_token(user.id, extra={"role": user.role})
    record_audit(
        db,
        actor=user,
        action="auth.login",
        entity_type="user",
        entity_id=user.id,
        details={"email": user.email},
    )
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/profile", response_model=UserRead)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    if payload.full_name:
        current_user.full_name = payload.full_name
    if payload.password:
        current_user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(current_user)
    record_audit(
        db,
        actor=current_user,
        action="auth.profile_updated",
        entity_type="user",
        entity_id=current_user.id,
        details=payload.model_dump(exclude_none=True, exclude={"password"}),
    )
    return UserRead.model_validate(current_user)
