from __future__ import annotations

from app.core.security import hash_password
from app.db.init_db import ensure_default_integrations
from app.db.session import SessionLocal
from app.ml.scoring import train_model
from app.models.entities import AlertSeverity, IncidentPriority, User, UserRole
from app.services.domain import create_alert, create_incident


def run_seed() -> None:
    db = SessionLocal()
    try:
        ensure_default_integrations(db)
        if db.query(User).count() == 0:
            admin = User(
                email="admin@example.com",
                full_name="AegisCore Admin",
                role=UserRole.ADMIN,
                password_hash=hash_password("Admin123!"),
            )
            analyst = User(
                email="analyst@example.com",
                full_name="Lead Analyst",
                role=UserRole.ANALYST,
                password_hash=hash_password("Analyst123!"),
            )
            viewer = User(
                email="viewer@example.com",
                full_name="Security Viewer",
                role=UserRole.VIEWER,
                password_hash=hash_password("Viewer123!"),
            )
            db.add_all([admin, analyst, viewer])
            db.commit()
            db.refresh(admin)
            db.refresh(analyst)

            alert_one = create_alert(
                db,
                title="Repeated SSH authentication failures",
                description="Multiple failed SSH logons observed from the same source IP.",
                source="wazuh",
                severity=AlertSeverity.HIGH.value,
                tags=["authentication_failed", "sshd"],
                raw_payload={},
                parsed_payload={"source_ip": "10.0.0.54"},
                asset_hostname="lab-web-03",
                asset_ip="10.0.0.54",
                actor=admin,
                ip_address="127.0.0.1",
            )
            alert_two = create_alert(
                db,
                title="Suspicious SMB admin share access",
                description="Suricata detected suspicious internal SMB admin share usage.",
                source="suricata",
                severity=AlertSeverity.CRITICAL.value,
                tags=["smb", "lateral-movement"],
                raw_payload={},
                parsed_payload={"dest_ip": "172.16.10.5"},
                asset_hostname="dc-01",
                asset_ip="172.16.10.5",
                actor=admin,
                ip_address="127.0.0.1",
            )
            create_incident(
                db,
                title="Active credential abuse investigation",
                description="Investigating repeated auth failures and SMB follow-on behavior.",
                priority=IncidentPriority.P2,
                assignee_id=analyst.id,
                linked_alert_ids=[alert_one.id, alert_two.id],
                evidence=[{"name": "auth-failures.csv", "type": "csv"}],
                actor=admin,
                ip_address="127.0.0.1",
            )

        train_model(db, "2026.03-seed")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
