from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_ip
from app.core.config import get_settings
from app.core.rate_limit import enforce_http_rate_limit, normalize_rate_limit_key, reset_rate_limit
from app.core.security import clear_auth_cookies, create_access_token, hash_password, set_auth_cookies, verify_password
from app.db.session import get_db
from app.models.entities import User
from app.schemas.domain import LoginRequest, ProfileUpdate, TokenResponse, UserRead
from app.services.audit import record_audit

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    response: Response,
    ip_address: str | None = Depends(get_optional_ip),
    db: Session = Depends(get_db),
) -> TokenResponse:
    settings = get_settings()
    rate_limit_key = normalize_rate_limit_key(ip_address, payload.email)
    enforce_http_rate_limit(
        "auth-login",
        rate_limit_key,
        limit=settings.login_rate_limit_attempts,
        window_seconds=settings.login_rate_limit_window_seconds,
    )
    user = db.query(User).filter(User.email == payload.email).one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        record_audit(
            db,
            actor=None,
            action="auth.login_failed",
            entity_type="session",
            entity_id=None,
            details={"email": payload.email, "reason": "invalid_credentials"},
            ip_address=ip_address,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    reset_rate_limit("auth-login", rate_limit_key)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, extra={"role": user.role})
    set_auth_cookies(response, token=token, role=str(user.role.value if hasattr(user.role, "value") else user.role))
    response.headers["Cache-Control"] = "no-store"
    record_audit(
        db,
        actor=user,
        action="auth.login",
        entity_type="user",
        entity_id=user.id,
        details={"email": user.email},
        ip_address=ip_address,
    )
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(response: Response, current_user: User = Depends(get_current_user)) -> UserRead:
    response.headers["Cache-Control"] = "no-store"
    return UserRead.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    clear_auth_cookies(response)
    response.headers["Cache-Control"] = "no-store"
    record_audit(
        db,
        actor=current_user,
        action="auth.logout",
        entity_type="user",
        entity_id=current_user.id,
        details={"email": current_user.email},
        ip_address=ip_address,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.patch("/profile", response_model=UserRead)
def update_profile(
    payload: ProfileUpdate,
    response: Response,
    db: Session = Depends(get_db),
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    if payload.full_name:
        current_user.full_name = payload.full_name
    if payload.password:
        current_user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(current_user)
    response.headers["Cache-Control"] = "no-store"
    record_audit(
        db,
        actor=current_user,
        action="auth.profile_updated",
        entity_type="user",
        entity_id=current_user.id,
        details=payload.model_dump(exclude_none=True, exclude={"password"}),
        ip_address=ip_address,
    )
    return UserRead.model_validate(current_user)
