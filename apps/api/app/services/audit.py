from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.entities import AuditLog, User


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
        details=details or {},
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
