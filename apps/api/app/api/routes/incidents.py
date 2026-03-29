from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_optional_ip, require_roles
from app.db.session import get_db
from app.models.entities import Alert, Incident, IncidentAlertLink, IncidentNote, User, UserRole
from app.schemas.domain import IncidentCreate, IncidentNoteCreate, IncidentNoteRead, IncidentRead, IncidentUpdate
from app.services.domain import add_incident_note, create_incident, update_incident

router = APIRouter()


@router.get("")
def list_incidents(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Incident).options(
        joinedload(Incident.assignee),
        joinedload(Incident.created_by),
        joinedload(Incident.notes).joinedload(IncidentNote.author),
        joinedload(Incident.alert_links).joinedload(IncidentAlertLink.alert),
    )
    if status_filter:
        query = query.filter(Incident.status == status_filter)

    total = query.count()
    items = query.order_by(Incident.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [IncidentRead.model_validate(item).model_dump() for item in items], "total": total}


@router.post("", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
def create_incident_route(
    payload: IncidentCreate,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
    db: Session = Depends(get_db),
) -> IncidentRead:
    incident = create_incident(
        db,
        title=payload.title,
        summary=payload.summary,
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        linked_alert_ids=payload.linked_alert_ids,
        evidence=payload.evidence,
        actor=current_user,
        ip_address=ip_address,
    )
    return IncidentRead.model_validate(incident)


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(incident_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> IncidentRead:
    incident = (
        db.query(Incident)
        .options(
            joinedload(Incident.assignee),
            joinedload(Incident.created_by),
            joinedload(Incident.notes).joinedload(IncidentNote.author),
            joinedload(Incident.alert_links).joinedload(IncidentAlertLink.alert),
        )
        .filter(Incident.id == incident_id)
        .one_or_none()
    )
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return IncidentRead.model_validate(incident)


@router.patch("/{incident_id}", response_model=IncidentRead)
def patch_incident(
    incident_id: str,
    payload: IncidentUpdate,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
    db: Session = Depends(get_db),
) -> IncidentRead:
    incident = db.query(Incident).filter(Incident.id == incident_id).one_or_none()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    updated = update_incident(db, incident, payload.model_dump(exclude_none=True), current_user, ip_address)
    return IncidentRead.model_validate(updated)


@router.post("/{incident_id}/notes", response_model=IncidentNoteRead, status_code=status.HTTP_201_CREATED)
def create_note(
    incident_id: str,
    payload: IncidentNoteCreate,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
    db: Session = Depends(get_db),
) -> IncidentNoteRead:
    incident = db.query(Incident).filter(Incident.id == incident_id).one_or_none()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    note = add_incident_note(
        db,
        incident=incident,
        actor=current_user,
        body=payload.body,
        is_timeline_event=payload.is_timeline_event,
        ip_address=ip_address,
    )
    return IncidentNoteRead.model_validate(note)
