from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.entities import Integration, IntegrationHealth, IntegrationType


DEFAULT_INTEGRATIONS = [
    ("Wazuh", "wazuh", IntegrationType.WAZUH),
    ("Suricata", "suricata", IntegrationType.SURICATA),
    ("Nmap Import", "nmap", IntegrationType.NMAP),
    ("Hydra Import", "hydra", IntegrationType.HYDRA),
]


def ensure_default_integrations(db: Session) -> None:
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
