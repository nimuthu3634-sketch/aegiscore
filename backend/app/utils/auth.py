from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.core.enums import UserRole
from app.core.security import get_token_payload
from app.services.auth import get_current_user_from_payload


def get_current_user(token_payload: dict = Depends(get_token_payload)) -> dict:
    return get_current_user_from_payload(token_payload)


def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive users cannot access this resource.",
        )

    return current_user


def require_roles(*roles: UserRole) -> Callable[[dict], dict]:
    def dependency(current_user: dict = Depends(get_current_active_user)) -> dict:
        user_role = current_user.get("role")
        if roles and user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )

        return current_user

    return dependency
