from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.entities import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_optional_ip(x_forwarded_for: str | None = Header(default=None)) -> str | None:
    if not x_forwarded_for:
        return None
    return x_forwarded_for.split(",")[0].strip()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
    except ValueError as error:
        raise credentials_error from error

    subject = payload.get("sub")
    if not subject:
        raise credentials_error

    user = db.query(User).filter(User.id == subject, User.is_active.is_(True)).one_or_none()
    if user is None:
        raise credentials_error

    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency
