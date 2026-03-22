from __future__ import annotations

from sqlalchemy import select

from app.core.enums import UserRole
from app.models.user import User
from app.services.mock_store import DEMO_USERS
from app.services.persistence import run_with_optional_db
from app.utils.time import ensure_utc


def _user_from_model(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "password_hash": user.password_hash,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": ensure_utc(user.created_at),
    }


def _load_persisted_users() -> list[dict]:
    def operation(db) -> list[dict]:
        users = db.scalars(select(User).order_by(User.created_at.desc())).all()
        return [_user_from_model(user) for user in users]

    return run_with_optional_db(operation, lambda: [])


def load_user_records() -> list[dict]:
    merged_users = {user["id"]: dict(user) for user in DEMO_USERS}

    for persisted_user in _load_persisted_users():
        if persisted_user["id"] in merged_users:
            merged_users[persisted_user["id"]] = {
                **merged_users[persisted_user["id"]],
                **persisted_user,
            }
        else:
            merged_users[persisted_user["id"]] = persisted_user

    return sorted(
        merged_users.values(),
        key=lambda user: user.get("created_at"),
        reverse=True,
    )


def get_user_by_email(email: str) -> dict | None:
    normalized_email = email.strip().casefold()
    return next(
        (
            user
            for user in load_user_records()
            if user["email"].strip().casefold() == normalized_email
        ),
        None,
    )


def get_user_by_id(user_id: str | None) -> dict | None:
    if user_id is None:
        return None

    return next((user for user in load_user_records() if user["id"] == user_id), None)


def get_user_name_lookup() -> dict[str, str]:
    return {user["id"]: user["full_name"] for user in load_user_records()}


def list_active_analysts() -> list[dict]:
    return [
        {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
        }
        for user in load_user_records()
        if user["role"] == UserRole.ANALYST and user.get("is_active", False)
    ]


def persist_user_record(user_record: dict) -> None:
    def operation(db) -> None:
        db.merge(
            User(
                id=user_record["id"],
                full_name=user_record["full_name"],
                email=user_record["email"],
                password_hash=user_record["password_hash"],
                role=user_record["role"],
                is_active=user_record.get("is_active", True),
                created_at=user_record["created_at"],
            )
        )
        db.commit()

    run_with_optional_db(operation, lambda: None)
