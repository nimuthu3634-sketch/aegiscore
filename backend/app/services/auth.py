from datetime import timedelta

from fastapi import HTTPException, status

from app.core.enums import UserRole
from app.core.security import create_access_token, get_password_hash, verify_password

DEMO_USERS = [
    {
        "id": "user-admin",
        "email": "admin@aegiscore.local",
        "full_name": "AegisCore Admin",
        "role": UserRole.ADMIN,
        "is_active": True,
        "hashed_password": get_password_hash("admin123"),
    },
    {
        "id": "user-analyst",
        "email": "analyst@aegiscore.local",
        "full_name": "AegisCore Analyst",
        "role": UserRole.ANALYST,
        "is_active": True,
        "hashed_password": get_password_hash("analyst123"),
    },
    {
        "id": "user-viewer",
        "email": "viewer@aegiscore.local",
        "full_name": "AegisCore Viewer",
        "role": UserRole.VIEWER,
        "is_active": True,
        "hashed_password": get_password_hash("viewer123"),
    },
]


def authenticate_user(email: str, password: str) -> dict:
    user = next((candidate for candidate in DEMO_USERS if candidate["email"] == email), None)

    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials for the demo auth scaffold.",
        )

    return user


def login_user(email: str, password: str) -> dict:
    user = authenticate_user(email=email, password=password)
    access_token = create_access_token(
        subject=user["email"],
        role=user["role"],
        expires_delta=timedelta(minutes=60),
    )
    return {**user, "access_token": access_token}


def list_demo_users() -> list[dict]:
    return DEMO_USERS
