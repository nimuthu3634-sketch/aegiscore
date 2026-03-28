from collections.abc import Callable

from fastapi import Depends, HTTPException, WebSocket, status

from app.core.enums import UserRole
from app.core.security import decode_access_token, get_token_payload
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


def _extract_websocket_token(websocket: WebSocket) -> str:
    authorization_header = websocket.headers.get("authorization", "")
    if authorization_header.lower().startswith("bearer "):
        token = authorization_header[7:].strip()
        if token:
            return token

    for query_key in ("token", "access_token"):
        token = websocket.query_params.get(query_key)
        if token:
            return token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication is required to access the live alert stream.",
    )


def get_current_websocket_user(websocket: WebSocket) -> dict:
    token = _extract_websocket_token(websocket)
    token_payload = decode_access_token(token)
    return get_current_user_from_payload(token_payload)


def get_current_active_websocket_user(websocket: WebSocket) -> dict:
    current_user = get_current_websocket_user(websocket)
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive users cannot access this resource.",
        )

    return current_user
