from __future__ import annotations

from app.db.session import SessionLocal
from app.models.entities import User
from app.ml.scoring import extract_features, score_alert
from app.services.domain import create_alert


def _admin_user(db):
    return db.query(User).filter(User.email == "admin@example.com").one()


def test_feature_engineering_captures_frequency_recurrence_and_user_sensitivity():
    with SessionLocal() as db:
        admin = _admin_user(db)
        first = create_alert(
            db,
            title="Repeated SSH authentication failures",
            description="Several failed administrator logins were recorded on a finance host.",
            source="wazuh",
            source_type="endpoint",
            event_type="authentication_failure",
            severity="high",
            tags=["authentication_failed", "credential"],
            raw_payload={"user": "finance-admin"},
            parsed_payload={"username": "finance-admin", "attempts": 5},
            asset_hostname="finance-core-01",
            asset_ip="10.10.1.15",
            actor=admin,
            ip_address="127.0.0.1",
        )
        second = create_alert(
            db,
            title="Repeated SSH authentication failures",
            description="Several failed administrator logins were recorded on a finance host.",
            source="wazuh",
            source_type="endpoint",
            event_type="authentication_failure",
            severity="high",
            tags=["authentication_failed", "credential"],
            raw_payload={"user": "finance-admin"},
            parsed_payload={"username": "finance-admin", "attempts": 6},
            asset_hostname="finance-core-01",
            asset_ip="10.10.1.15",
            actor=admin,
            ip_address="127.0.0.1",
        )

        asset = first.asset
        assert asset is not None
        asset.criticality = 5
        db.commit()

        features = extract_features(
            {
                "title": "Repeated SSH authentication failures",
                "description": "Another burst of failed privileged logins was detected.",
                "source": "wazuh",
                "source_type": "endpoint",
                "event_type": "authentication_failure",
                "severity": "high",
                "tags": ["authentication_failed", "credential"],
                "raw_payload": {"user": "finance-admin"},
                "parsed_payload": {"username": "finance-admin"},
                "occurred_at": second.occurred_at,
                "asset_id": asset.id,
                "asset_criticality": asset.criticality,
            },
            db=db,
            asset=asset,
        )

        assert features["frequency_1h"] >= 2
        assert features["recurrence_24h"] >= 2
        assert features["asset_criticality"] == 5
        assert features["user_sensitivity"] >= 4


def test_scoring_returns_explainable_high_risk_assessment():
    with SessionLocal() as db:
        admin = _admin_user(db)
        first = create_alert(
            db,
            title="Repeated SSH authentication failures",
            description="Failed privileged logins detected on a critical application server.",
            source="wazuh",
            source_type="endpoint",
            event_type="authentication_failure",
            severity="high",
            tags=["authentication_failed", "credential"],
            raw_payload={"user": "finance-admin"},
            parsed_payload={"username": "finance-admin"},
            asset_hostname="payments-app-01",
            asset_ip="10.20.5.10",
            actor=admin,
            ip_address="127.0.0.1",
        )
        create_alert(
            db,
            title="Suspicious SMB lateral movement",
            description="Network telemetry saw administrative SMB traffic touching the same host.",
            source="suricata",
            source_type="network",
            event_type="lateral_movement",
            severity="critical",
            tags=["smb", "lateral-movement"],
            raw_payload={"dest_ip": "10.20.5.10"},
            parsed_payload={"dest_ip": "10.20.5.10"},
            asset_hostname="payments-app-01",
            asset_ip="10.20.5.10",
            actor=admin,
            ip_address="127.0.0.1",
        )

        asset = first.asset
        assert asset is not None
        asset.criticality = 5
        db.commit()

        assessment = score_alert(
            {
                "title": "Repeated SSH authentication failures",
                "description": "Another burst of failed privileged logins was detected on the same high-value server.",
                "source": "wazuh",
                "source_type": "endpoint",
                "event_type": "authentication_failure",
                "severity": "high",
                "tags": ["authentication_failed", "credential"],
                "raw_payload": {"user": "finance-admin"},
                "parsed_payload": {"username": "finance-admin"},
                "occurred_at": first.occurred_at,
                "asset_id": asset.id,
                "asset_criticality": asset.criticality,
                "asset_hostname": asset.hostname,
            },
            db=db,
            asset=asset,
        )

        factor_names = {factor["factor"] for factor in assessment.explanations}
        assert 0 <= assessment.score <= 100
        assert assessment.band in {"high", "critical"}
        assert "high_value_asset_involved" in factor_names
        assert "multiple_correlated_sources" in factor_names
        assert assessment.summary


def test_ml_overview_and_recalculate_endpoints(client, admin_token, analyst_token):
    create_response = client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Suspicious exposed admin interface",
            "description": "Nmap lab import found an exposed administrative web service on a finance host.",
            "source": "nmap",
            "source_type": "lab-import",
            "event_type": "service_exposure",
            "severity": "medium",
            "asset_hostname": "finance-edge-01",
            "asset_ip": "10.30.0.12",
            "tags": ["exposure", "admin-panel"],
            "raw_payload": {"port": 8443},
            "parsed_payload": {"port": 8443, "lab_imported": True},
        },
    )

    assert create_response.status_code == 201

    overview_response = client.get("/api/v1/ml/overview", headers={"Authorization": f"Bearer {admin_token}"})
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["summary"]["total_alerts"] >= 1
    assert "risk_distribution" in overview
    assert overview["active_model"]["feature_version"]

    analyst_recalc = client.post("/api/v1/ml/recalculate", headers={"Authorization": f"Bearer {analyst_token}"}, json={})
    assert analyst_recalc.status_code == 403

    admin_recalc = client.post(
        "/api/v1/ml/recalculate",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"open_only": True},
    )
    assert admin_recalc.status_code == 200
    assert admin_recalc.json()["rescored_alerts"] >= 1
