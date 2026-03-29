from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_optional_ip, require_roles
from app.db.session import get_db
from app.models.entities import Alert, AlertComment, IncidentAlertLink, User, UserRole
from app.schemas.domain import (
    AlertCommentCreate,
    AlertCommentRead,
    AlertCreate,
    AlertListResponse,
    AlertRead,
    AlertUpdate,
    IncidentCreate,
    IncidentRead,
)
from app.services.domain import add_alert_comment, broadcast_alert_event, create_alert, create_incident, update_alert

router = APIRouter()


@router.get("", response_model=AlertListResponse)
def list_alerts(
    q: str | None = Query(default=None),
    source: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    assignee_id: str | None = Query(default=None),
    incident_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AlertListResponse:
    query = db.query(Alert).options(
        joinedload(Alert.asset),
        joinedload(Alert.assignee),
        joinedload(Alert.integration),
        joinedload(Alert.comments).joinedload(AlertComment.author),
        joinedload(Alert.response_recommendations),
        joinedload(Alert.incident_links).joinedload(IncidentAlertLink.incident),
    )
    if q:
        query = query.filter(or_(Alert.title.ilike(f"%{q}%"), Alert.description.ilike(f"%{q}%")))
    if source:
        query = query.filter(Alert.source == source)
    if source_type:
        query = query.filter(Alert.source_type == source_type)
    if event_type:
        query = query.filter(Alert.event_type == event_type)
    if severity:
        query = query.filter(Alert.severity == severity)
    if status_filter:
        query = query.filter(Alert.status == status_filter)
    if assignee_id:
        query = query.filter(Alert.assigned_to_id == assignee_id)
    if tag:
        query = query.filter(Alert.tags.contains([tag]))
    if incident_id:
        query = query.join(Alert.incident_links).filter(IncidentAlertLink.incident_id == incident_id)

    total = query.count()
    items = query.order_by(Alert.detected_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return AlertListResponse(
        items=[AlertRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
async def create_alert_route(
    payload: AlertCreate,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
    db: Session = Depends(get_db),
) -> AlertRead:
    alert = create_alert(
        db,
        title=payload.title,
        description=payload.description,
        source=payload.source,
        source_type=payload.source_type,
        event_type=payload.event_type,
        severity=payload.severity.value,
        occurred_at=payload.occurred_at,
        tags=payload.tags,
        raw_payload=payload.raw_payload,
        parsed_payload=payload.parsed_payload,
        asset_hostname=payload.asset_hostname,
        asset_ip=payload.asset_ip,
        actor=current_user,
        ip_address=ip_address,
    )
    await broadcast_alert_event(alert, "created")
    return AlertRead.model_validate(alert)


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert(alert_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AlertRead:
    alert = (
        db.query(Alert)
        .options(
            joinedload(Alert.asset),
            joinedload(Alert.assignee),
            joinedload(Alert.integration),
            joinedload(Alert.comments).joinedload(AlertComment.author),
            joinedload(Alert.response_recommendations),
            joinedload(Alert.incident_links).joinedload(IncidentAlertLink.incident),
        )
        .filter(Alert.id == alert_id)
        .one_or_none()
    )
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return AlertRead.model_validate(alert)


@router.patch("/{alert_id}", response_model=AlertRead)
async def patch_alert(
    alert_id: str,
    payload: AlertUpdate,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
    db: Session = Depends(get_db),
) -> AlertRead:
    alert = db.query(Alert).filter(Alert.id == alert_id).one_or_none()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    updated = update_alert(db, alert, payload=payload.model_dump(exclude_none=False), actor=current_user, ip_address=ip_address)
    await broadcast_alert_event(updated, "updated")
    return AlertRead.model_validate(updated)


@router.post("/{alert_id}/comments", response_model=AlertCommentRead, status_code=status.HTTP_201_CREATED)
def comment_on_alert(
    alert_id: str,
    payload: AlertCommentCreate,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
    db: Session = Depends(get_db),
) -> AlertCommentRead:
    alert = db.query(Alert).filter(Alert.id == alert_id).one_or_none()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    comment = add_alert_comment(db, alert=alert, actor=current_user, body=payload.body, ip_address=ip_address)
    return AlertCommentRead.model_validate(comment)


@router.post("/{alert_id}/incident", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
def create_incident_from_alert(
    alert_id: str,
    payload: IncidentCreate,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
    db: Session = Depends(get_db),
) -> IncidentRead:
    alert = db.query(Alert).filter(Alert.id == alert_id).one_or_none()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    incident = create_incident(
        db,
        title=payload.title or f"Investigation for {alert.title}",
        description=payload.description,
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        linked_alert_ids=[alert_id, *[identifier for identifier in payload.linked_alert_ids if identifier != alert_id]],
        evidence=payload.evidence,
        actor=current_user,
        ip_address=ip_address,
    )
    return IncidentRead.model_validate(incident)
