from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import Response
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12, deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode: dict[str, Any] = {
        "sub": subject,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid4()),
        "type": "access",
    }
    if extra:
        to_encode.update(extra)
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, *, expected_type: str = "access") -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={
                "require_sub": True,
                "require_exp": True,
                "require_iat": True,
                "require_nbf": True,
                "require_iss": True,
                "require_aud": True,
                "require_jti": True,
            },
        )
    except JWTError as error:  # pragma: no cover - exercised via API behavior
        raise ValueError("Invalid access token") from error
    if expected_type and payload.get("type") != expected_type:
        raise ValueError("Invalid access token")
    return payload


def set_auth_cookies(response: Response, *, token: str, role: str) -> None:
    settings = get_settings()
    max_age = settings.access_token_expire_minutes * 60
    cookie_options = {
        "path": "/",
        "max_age": max_age,
        "secure": settings.auth_cookie_secure,
        "samesite": settings.auth_cookie_samesite,
    }
    if settings.auth_cookie_domain:
        cookie_options["domain"] = settings.auth_cookie_domain

    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        **cookie_options,
    )
    response.set_cookie(
        key=settings.auth_role_cookie_name,
        value=role,
        httponly=True,
        **cookie_options,
    )


def clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    delete_options = {"path": "/"}
    if settings.auth_cookie_domain:
        delete_options["domain"] = settings.auth_cookie_domain

    response.delete_cookie(settings.auth_cookie_name, **delete_options)
    response.delete_cookie(settings.auth_role_cookie_name, **delete_options)
