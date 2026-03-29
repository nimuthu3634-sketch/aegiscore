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
            continue
        db.add(
            Integration(
                name=name,
                slug=slug,
                type=integration_type,
                health_status=IntegrationHealth.HEALTHY,
                enabled=True,
                description=f"{name} defensive telemetry source",
            )
        )
    db.commit()
