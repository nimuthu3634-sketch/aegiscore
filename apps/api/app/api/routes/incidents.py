from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_optional_ip, require_roles
from app.db.session import get_db
from app.models.entities import Alert, Incident, IncidentAlertLink, IncidentEvent, User, UserRole
from app.schemas.domain import (
    IncidentCreate,
    IncidentEventCreate,
    IncidentEventRead,
    IncidentListResponse,
    IncidentRead,
    IncidentUpdate,
)
from app.services.domain import add_incident_note, create_incident, update_incident

router = APIRouter()


@router.get("", response_model=IncidentListResponse)
def list_incidents(
    q: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    assignee_id: str | None = Query(default=None),
    linked_alert_id: str | None = Query(default=None),
    linked_asset_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IncidentListResponse:
    query = db.query(Incident).options(
        joinedload(Incident.assignee),
        joinedload(Incident.created_by),
        joinedload(Incident.events).joinedload(IncidentEvent.author),
        joinedload(Incident.alert_links).joinedload(IncidentAlertLink.alert).joinedload(Alert.asset),
    )
    if q:
        query = query.filter(or_(Incident.title.ilike(f"%{q}%"), Incident.description.ilike(f"%{q}%")))
    if status_filter:
        query = query.filter(Incident.status == status_filter)
    if priority:
        query = query.filter(Incident.priority == priority)
    if assignee_id:
        query = query.filter(Incident.assignee_id == assignee_id)
    if linked_alert_id:
        query = query.join(Incident.alert_links).filter(IncidentAlertLink.alert_id == linked_alert_id)
    if linked_asset_id:
        query = query.join(Incident.alert_links).join(IncidentAlertLink.alert).filter(Alert.asset_id == linked_asset_id)

    total = query.count()
    items = query.order_by(Incident.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return IncidentListResponse(
        items=[IncidentRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


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
        description=payload.description,
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
            joinedload(Incident.events).joinedload(IncidentEvent.author),
            joinedload(Incident.alert_links).joinedload(IncidentAlertLink.alert).joinedload(Alert.asset),
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


@router.post("/{incident_id}/events", response_model=IncidentEventRead, status_code=status.HTTP_201_CREATED)
def create_event(
    incident_id: str,
    payload: IncidentEventCreate,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
    db: Session = Depends(get_db),
) -> IncidentEventRead:
    incident = db.query(Incident).filter(Incident.id == incident_id).one_or_none()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    event = add_incident_note(
        db,
        incident=incident,
        actor=current_user,
        body=payload.body,
        is_timeline_event=payload.is_timeline_event,
        ip_address=ip_address,
        event_type=payload.event_type,
        event_metadata=payload.event_metadata,
    )
    return IncidentEventRead.model_validate(event)
