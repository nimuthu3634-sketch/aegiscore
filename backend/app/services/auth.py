from fastapi import HTTPException, status

from app.core.security import TOKEN_TYPE, create_access_token, get_password_hash, verify_password
from app.services.mock_store import DEMO_USERS, build_user_record
from app.services.users import get_user_by_email, load_user_records, persist_user_record


def list_demo_users() -> list[dict]:
    return load_user_records()


def authenticate_user(email: str, password: str) -> dict:
    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    return user


def login_user(email: str, password: str) -> dict:
    user = authenticate_user(email=email, password=password)
    access_token = create_access_token(subject=user["email"], role=user["role"])
    return {**user, "access_token": access_token, "token_type": TOKEN_TYPE}


def register_user(full_name: str, email: str, password: str, role) -> dict:
    if get_user_by_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists.",
        )

    user = build_user_record(
        full_name=full_name,
        email=email,
        password_hash=get_password_hash(password),
        role=role,
    )
    DEMO_USERS.append(user)
    persist_user_record(user)
    access_token = create_access_token(subject=user["email"], role=user["role"])
    return {**user, "access_token": access_token, "token_type": TOKEN_TYPE}


def get_current_user_from_payload(payload: dict) -> dict:
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing a subject.",
        )

    user = get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for token subject.",
        )

    return user
