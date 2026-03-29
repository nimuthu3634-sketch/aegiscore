from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_optional_ip, require_roles
from app.db.session import get_db
from app.models.entities import Alert, Asset, Incident, IncidentAlertLink, IncidentEvent, Integration, IntegrationRun, LogEntry, User, UserRole
from app.schemas.domain import (
    AssetListResponse,
    AssetRead,
    ImportResult,
    IntegrationConfigUpdate,
    IntegrationListResponse,
    IntegrationRead,
    IntegrationRunListResponse,
    IntegrationRunRead,
    LogEntryListResponse,
    LogEntryRead,
)
from app.services.integrations import import_integration_file, sync_integration, update_integration_configuration
from app.services.domain import (
    build_dashboard_summary,
    incident_summary_text,
    render_alerts_csv,
    render_dashboard_csv,
)

router = APIRouter()


@router.get("/logs", response_model=LogEntryListResponse)
def list_logs(
    q: str | None = Query(default=None),
    source: str | None = Query(default=None),
    category: str | None = Query(default=None),
    asset_id: str | None = Query(default=None),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogEntryListResponse:
    query = db.query(LogEntry).options(joinedload(LogEntry.asset))
    if q:
        query = query.filter(or_(LogEntry.message.ilike(f"%{q}%"), LogEntry.category.ilike(f"%{q}%")))
    if source:
        query = query.filter(LogEntry.source == source)
    if category:
        query = query.filter(LogEntry.category == category)
    if asset_id:
        query = query.filter(LogEntry.asset_id == asset_id)
    if start:
        query = query.filter(LogEntry.event_timestamp >= start)
    if end:
        query = query.filter(LogEntry.event_timestamp <= end)

    total = query.count()
    items = query.order_by(LogEntry.event_timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return LogEntryListResponse(
        items=[LogEntryRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/assets", response_model=AssetListResponse)
def list_assets(
    q: str | None = Query(default=None),
    risk_min: float | None = Query(default=None, ge=0, le=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssetListResponse:
    query = db.query(Asset)
    if q:
        query = query.filter(or_(Asset.hostname.ilike(f"%{q}%"), Asset.ip_address.ilike(f"%{q}%")))
    if risk_min is not None:
        query = query.filter(Asset.risk_score >= risk_min)
    total = query.count()
    items = query.order_by(Asset.risk_score.desc(), Asset.hostname.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return AssetListResponse(items=[AssetRead.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


@router.get("/assets/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AssetRead:
    asset = db.query(Asset).filter(Asset.id == asset_id).one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return AssetRead.model_validate(asset)


@router.get("/integrations", response_model=IntegrationListResponse)
def list_integrations(
    type_filter: str | None = Query(default=None, alias="type"),
    health: str | None = Query(default=None),
    enabled: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IntegrationListResponse:
    query = db.query(Integration).options(joinedload(Integration.runs))
    if type_filter:
        query = query.filter(Integration.type == type_filter)
    if health:
        query = query.filter(Integration.health_status == health)
    if enabled is not None:
        query = query.filter(Integration.enabled.is_(enabled))
    total = query.count()
    items = query.order_by(Integration.name.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return IntegrationListResponse(
        items=[IntegrationRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/integrations/{slug}", response_model=IntegrationRead)
def get_integration(slug: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> IntegrationRead:
    integration = db.query(Integration).options(joinedload(Integration.runs)).filter(Integration.slug == slug).one_or_none()
    if integration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    return IntegrationRead.model_validate(integration)


@router.get("/integrations/{slug}/history", response_model=IntegrationRunListResponse)
def integration_history(
    slug: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IntegrationRunListResponse:
    integration = db.query(Integration).filter(Integration.slug == slug).one_or_none()
    if integration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    query = db.query(IntegrationRun).filter(IntegrationRun.integration_id == integration.id)
    total = query.count()
    runs = query.order_by(IntegrationRun.started_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return IntegrationRunListResponse(
        items=[IntegrationRunRead.model_validate(item) for item in runs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/integrations/{slug}", response_model=IntegrationRead)
def update_integration(
    slug: str,
    payload: IntegrationConfigUpdate,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> IntegrationRead:
    integration = update_integration_configuration(
        db,
        slug=slug,
        payload=payload,
        actor=current_user,
        ip_address=ip_address,
    )
    return IntegrationRead.model_validate(integration)


@router.post("/integrations/{slug}/sync", response_model=ImportResult, status_code=status.HTTP_202_ACCEPTED)
async def sync_integration_route(
    slug: str,
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
    db: Session = Depends(get_db),
) -> ImportResult:
    summary = await sync_integration(
        db,
        slug=slug,
        actor=current_user,
        ip_address=ip_address,
    )
    return ImportResult(
        integration=summary.integration,
        run_id=summary.run_id,
        mode=summary.mode,
        status=summary.status,
        alerts_created=summary.alerts_created,
        alerts_updated=summary.alerts_updated,
        logs_created=summary.logs_created,
        assets_touched=summary.assets_touched,
        incident_candidates=summary.incident_candidates,
        normalized_records=summary.normalized_records,
        input_format=summary.input_format,
        imported_lab_data=summary.imported_lab_data,
    )


@router.post("/integrations/{slug}/import", response_model=ImportResult, status_code=status.HTTP_202_ACCEPTED)
async def import_integration(
    slug: str,
    file: UploadFile = File(...),
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
    db: Session = Depends(get_db),
) -> ImportResult:
    content = await file.read()
    summary = await import_integration_file(
        db,
        slug=slug,
        filename=file.filename or f"{slug}-import.json",
        raw_bytes=content,
        actor=current_user,
        ip_address=ip_address,
    )
    return ImportResult(
        integration=summary.integration,
        run_id=summary.run_id,
        mode=summary.mode,
        status=summary.status,
        alerts_created=summary.alerts_created,
        alerts_updated=summary.alerts_updated,
        logs_created=summary.logs_created,
        assets_touched=summary.assets_touched,
        incident_candidates=summary.incident_candidates,
        normalized_records=summary.normalized_records,
        input_format=summary.input_format,
        imported_lab_data=summary.imported_lab_data,
    )


@router.get("/reports/alerts.csv")
def export_alerts(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    alerts = db.query(Alert).options(joinedload(Alert.asset)).order_by(Alert.detected_at.desc()).all()
    return Response(render_alerts_csv(alerts), media_type="text/csv")


@router.get("/reports/dashboard.csv")
def export_dashboard(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    return Response(render_dashboard_csv(build_dashboard_summary(db)), media_type="text/csv")


@router.get("/reports/incidents/{incident_id}/summary")
def export_incident_summary(incident_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    incident = (
        db.query(Incident)
        .options(joinedload(Incident.events).joinedload(IncidentEvent.author), joinedload(Incident.alert_links).joinedload(IncidentAlertLink.alert))
        .filter(Incident.id == incident_id)
        .one_or_none()
    )
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return Response(incident_summary_text(incident), media_type="text/plain")
