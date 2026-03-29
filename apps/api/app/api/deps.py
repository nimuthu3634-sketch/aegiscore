from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.entities import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_optional_ip(
    request: Request,
    x_forwarded_for: str | None = Header(default=None),
    x_real_ip: str | None = Header(default=None),
) -> str | None:
    for value in (x_forwarded_for, x_real_ip):
        if value:
            return value.split(",")[0].strip()
    return request.client.host if request.client else None


def get_current_user(request: Request, token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    settings = get_settings()
    access_token = token or request.cookies.get(settings.auth_cookie_name)
    if not access_token:
        raise credentials_error

    try:
        payload = decode_access_token(access_token)
    except ValueError as error:
        raise credentials_error from error

    subject = payload.get("sub")
    if not subject:
        raise credentials_error

    user = db.query(User).filter(User.id == subject, User.is_active.is_(True)).one_or_none()
    if user is None:
        raise credentials_error
    expected_role = user.role.value if hasattr(user.role, "value") else str(user.role)
    if payload.get("role") and str(payload["role"]) != expected_role:
        raise credentials_error

    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency
