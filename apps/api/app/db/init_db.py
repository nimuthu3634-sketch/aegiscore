from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.entities import Integration, IntegrationHealth, IntegrationType, Role, UserRole


DEFAULT_ROLES = [
    (UserRole.ADMIN, "Full administrative access to users, configuration, and AI jobs."),
    (UserRole.ANALYST, "Operational access to triage alerts, manage incidents, and import telemetry."),
    (UserRole.VIEWER, "Read-only access to dashboards, alerts, incidents, and reports."),
]

DEFAULT_INTEGRATIONS = [
    ("Wazuh", "wazuh", IntegrationType.WAZUH),
    ("Suricata", "suricata", IntegrationType.SURICATA),
    ("Nmap Import", "nmap", IntegrationType.NMAP),
    ("Hydra Import", "hydra", IntegrationType.HYDRA),
]


def default_integration_config(slug: str) -> dict:
    if slug in {IntegrationType.WAZUH.value, IntegrationType.SURICATA.value}:
        return {
            "endpoint_url": None,
            "auth_type": "none",
            "username": None,
            "password": None,
            "api_token": None,
            "verify_tls": True,
            "timeout_seconds": 15,
            "lookback_minutes": 60,
            "request_headers": {},
            "query_params": {},
        }
    return {"import_only": True}


def ensure_default_roles(db: Session) -> None:
    for role_name, description in DEFAULT_ROLES:
        existing = db.query(Role).filter(Role.name == role_name).one_or_none()
        if existing:
            continue
        db.add(Role(name=role_name, description=description))
    db.commit()


def ensure_default_integrations(db: Session) -> None:
    ensure_default_roles(db)
    for name, slug, integration_type in DEFAULT_INTEGRATIONS:
        existing = db.query(Integration).filter(Integration.slug == slug).one_or_none()
        if existing:
            if not existing.config:
                existing.config = default_integration_config(slug)
            if slug in {IntegrationType.NMAP.value, IntegrationType.HYDRA.value} and not existing.last_error:
                existing.last_error = "Import-only lab connector. Remote execution is disabled."
                existing.health_status = IntegrationHealth.HEALTHY
            continue
        db.add(
            Integration(
                name=name,
                slug=slug,
                type=integration_type,
                health_status=IntegrationHealth.OFFLINE if slug in {IntegrationType.WAZUH.value, IntegrationType.SURICATA.value} else IntegrationHealth.HEALTHY,
                enabled=True,
                description=(
                    f"{name} defensive telemetry source"
                    if slug in {IntegrationType.WAZUH.value, IntegrationType.SURICATA.value}
                    else f"{name} import-only lab connector"
                ),
                last_error=(
                    "Configuration required before manual sync."
                    if slug in {IntegrationType.WAZUH.value, IntegrationType.SURICATA.value}
                    else "Import-only lab connector. Remote execution is disabled."
                ),
                config=default_integration_config(slug),
            )
        )
    db.commit()
