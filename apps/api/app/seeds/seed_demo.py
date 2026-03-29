from __future__ import annotations

from app.core.security import hash_password
from app.db.base import Base
from app.db.init_db import ensure_default_integrations
from app.db.session import SessionLocal, engine
from app.ml.scoring import train_model
from app.models.entities import Alert, Incident, AlertSeverity, IncidentPriority, ModelMetadata, User, UserRole
from app.services.domain import create_alert, create_incident, rescore_alerts


def run_seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_default_integrations(db)
        if db.query(User).count() == 0:
            db.add_all(
                [
                    User(
                        email="admin@example.com",
                        full_name="AegisCore Admin",
                        role=UserRole.ADMIN,
                        password_hash=hash_password("Admin123!"),
                    ),
                    User(
                        email="analyst@example.com",
                        full_name="Lead Analyst",
                        role=UserRole.ANALYST,
                        password_hash=hash_password("Analyst123!"),
                    ),
                    User(
                        email="viewer@example.com",
                        full_name="Security Viewer",
                        role=UserRole.VIEWER,
                        password_hash=hash_password("Viewer123!"),
                    ),
                ]
            )
            db.commit()

        admin = db.query(User).filter(User.email == "admin@example.com").one()
        analyst = db.query(User).filter(User.email == "analyst@example.com").one()

        if db.query(Alert).count() == 0:
            seeded_alerts = [
                create_alert(
                    db,
                    title="Repeated SSH authentication failures",
                    description="Multiple failed SSH logons observed from the same source IP within a short time window.",
                    source="wazuh",
                    source_type="endpoint-telemetry",
                    event_type="authentication-failure",
                    severity=AlertSeverity.HIGH.value,
                    tags=["authentication_failed", "sshd", "repeated"],
                    raw_payload={"sensor": "wazuh-lab"},
                    parsed_payload={"source_ip": "10.0.0.54", "attempt_count": 14},
                    asset_hostname="lab-web-03",
                    asset_ip="10.0.0.54",
                    actor=admin,
                    ip_address="127.0.0.1",
                ),
                create_alert(
                    db,
                    title="Suspicious SMB admin share access",
                    description="Suricata detected unusual SMB administrative share activity between internal hosts.",
                    source="suricata",
                    source_type="network-telemetry",
                    event_type="lateral-movement-indicator",
                    severity=AlertSeverity.CRITICAL.value,
                    tags=["smb", "lateral-movement", "suricata"],
                    raw_payload={"sensor": "suricata-lab"},
                    parsed_payload={"dest_ip": "172.16.10.5", "protocol": "tcp"},
                    asset_hostname="dc-01",
                    asset_ip="172.16.10.5",
                    actor=admin,
                    ip_address="127.0.0.1",
                ),
                create_alert(
                    db,
                    title="Nmap import: external exposure review",
                    description="Imported Nmap lab result flagged exposed management ports on a perimeter system.",
                    source="nmap",
                    source_type="lab-import",
                    event_type="nmap-import",
                    severity=AlertSeverity.MEDIUM.value,
                    tags=["nmap", "lab-imported", "exposure"],
                    raw_payload={"lab_imported": True},
                    parsed_payload={"open_ports": [22, 3389], "execution_supported": False},
                    asset_hostname="edge-gateway-01",
                    asset_ip="10.10.10.5",
                    actor=admin,
                    ip_address="127.0.0.1",
                ),
                create_alert(
                    db,
                    title="Hydra import: valid credential observed",
                    description="Imported Hydra lab output captured a successful credential match during a controlled classroom exercise.",
                    source="hydra",
                    source_type="lab-import",
                    event_type="hydra-import",
                    severity=AlertSeverity.HIGH.value,
                    tags=["hydra", "lab-imported", "credential"],
                    raw_payload={"lab_imported": True},
                    parsed_payload={"username": "analyst_demo", "has_password_match": True, "execution_supported": False},
                    asset_hostname="lab-ssh-01",
                    asset_ip="10.20.10.11",
                    actor=admin,
                    ip_address="127.0.0.1",
                ),
            ]

            create_incident(
                db,
                title="Active credential abuse investigation",
                description="Investigating repeated authentication failures and associated high-risk credential telemetry.",
                priority=IncidentPriority.P2,
                assignee_id=analyst.id,
                linked_alert_ids=[seeded_alerts[0].id, seeded_alerts[3].id],
                evidence=[{"name": "auth-failures.csv", "type": "csv"}, {"name": "hydra-lab-output.txt", "type": "txt"}],
                actor=admin,
                ip_address="127.0.0.1",
            )
            create_incident(
                db,
                title="Potential internal lateral movement",
                description="Reviewing Suricata SMB findings against domain controller telemetry and asset criticality.",
                priority=IncidentPriority.P1,
                assignee_id=analyst.id,
                linked_alert_ids=[seeded_alerts[1].id],
                evidence=[{"name": "suricata-smb.json", "type": "json"}],
                actor=admin,
                ip_address="127.0.0.1",
            )

        if db.query(ModelMetadata).filter(ModelMetadata.version == "2026.03-seed").one_or_none() is None:
            train_model(db, "2026.03-seed")
        if db.query(Incident).count() >= 1:
            rescore_alerts(db, open_only=False)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
