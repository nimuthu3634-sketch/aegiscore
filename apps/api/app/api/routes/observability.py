from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_optional_ip, require_roles
from app.db.session import get_db
from app.models.entities import Alert, Asset, Incident, IncidentAlertLink, Integration, IntegrationRun, LogEntry, User, UserRole
from app.schemas.domain import AssetRead, ImportResult, IntegrationRead, IntegrationRunRead, LogEntryRead
from app.services.domain import (
    build_dashboard_summary,
    import_telemetry,
    incident_summary_text,
    render_alerts_csv,
    render_dashboard_csv,
)

router = APIRouter()


@router.get("/logs")
def list_logs(
    q: str | None = Query(default=None),
    source: str | None = Query(default=None),
    asset_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(LogEntry).options(joinedload(LogEntry.asset))
    if q:
        query = query.filter(or_(LogEntry.message.ilike(f"%{q}%"), LogEntry.category.ilike(f"%{q}%")))
    if source:
        query = query.filter(LogEntry.source == source)
    if asset_id:
        query = query.filter(LogEntry.asset_id == asset_id)

    total = query.count()
    items = query.order_by(LogEntry.event_timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [LogEntryRead.model_validate(item).model_dump() for item in items], "total": total}


@router.get("/assets")
def list_assets(
    q: str | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Asset)
    if q:
        query = query.filter(or_(Asset.hostname.ilike(f"%{q}%"), Asset.ip_address.ilike(f"%{q}%")))
    items = query.order_by(Asset.risk_score.desc(), Asset.hostname.asc()).all()
    return {"items": [AssetRead.model_validate(item).model_dump() for item in items], "total": len(items)}


@router.get("/assets/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AssetRead:
    asset = db.query(Asset).filter(Asset.id == asset_id).one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return AssetRead.model_validate(asset)


@router.get("/integrations")
def list_integrations(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    items = db.query(Integration).options(joinedload(Integration.runs)).order_by(Integration.name.asc()).all()
    return {"items": [IntegrationRead.model_validate(item).model_dump() for item in items], "total": len(items)}


@router.get("/integrations/{slug}/history")
def integration_history(slug: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    integration = db.query(Integration).filter(Integration.slug == slug).one_or_none()
    if integration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    runs = db.query(IntegrationRun).filter(IntegrationRun.integration_id == integration.id).order_by(IntegrationRun.started_at.desc()).all()
    return {"items": [IntegrationRunRead.model_validate(item).model_dump() for item in runs], "total": len(runs)}


@router.post("/integrations/{slug}/import", response_model=ImportResult, status_code=status.HTTP_202_ACCEPTED)
async def import_integration(
    slug: str,
    file: UploadFile = File(...),
    ip_address: str | None = Depends(get_optional_ip),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
    db: Session = Depends(get_db),
) -> ImportResult:
    content = await file.read()
    summary = import_telemetry(
        db,
        source=slug,
        filename=file.filename or f"{slug}-import.json",
        raw_bytes=content,
        actor=current_user,
        ip_address=ip_address,
    )
    return ImportResult(
        integration=summary.integration,
        run_id=summary.run_id,
        alerts_created=summary.alerts_created,
        logs_created=summary.logs_created,
        assets_touched=summary.assets_touched,
        incident_candidates=summary.incident_candidates,
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
        .options(joinedload(Incident.notes), joinedload(Incident.alert_links).joinedload(IncidentAlertLink.alert))
        .filter(Incident.id == incident_id)
        .one_or_none()
    )
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return Response(incident_summary_text(incident), media_type="text/plain")
