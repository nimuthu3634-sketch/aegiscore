from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.entities import AuditLog, User

SENSITIVE_DETAIL_TOKENS = {"password", "token", "secret", "key", "authorization", "cookie"}


def _sanitize_details(value, *, field_name: str | None = None):
    if isinstance(value, dict):
        sanitized: dict = {}
        for key, item in value.items():
            lowered = str(key).lower()
            sensitive = any(token in lowered for token in SENSITIVE_DETAIL_TOKENS) and not lowered.startswith("has_")
            sanitized[key] = "***" if sensitive and item not in {None, True, False} else _sanitize_details(item, field_name=lowered)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_details(item, field_name=field_name) for item in value]
    if field_name and any(token in field_name for token in SENSITIVE_DETAIL_TOKENS) and value not in {None, True, False}:
        return "***"
    return value


def record_audit(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_user_id=actor.id if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=_sanitize_details(details or {}),
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
