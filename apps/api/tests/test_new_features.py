"""Tests for changes made in the working-system completion pass.

Covers:
- Incident reference uniqueness (no duplicate INC-NNNN)
- Asset risk recalculation uses SQL aggregation (db param path)
- Response action status is "recorded" not "simulated"
- Integration test endpoint returns expected structure
- Rate limiter fallback (in-memory when Redis unavailable)
- Retrain audit entry appears after queueing
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.rate_limit import _InMemoryRateLimiter
from app.db.session import SessionLocal
from app.models.entities import Alert, AlertSeverity, AlertStatus, Asset, Incident, IncidentStatus
from app.services.domain import _refresh_asset_risk, create_incident
from app.services import integrations as integration_service
from app.models.entities import IncidentPriority, User, UserRole
from app.core.security import hash_password


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_user(db, email: str, role: UserRole = UserRole.ANALYST) -> User:
    user = User(email=email, full_name="Test User", role=role, password_hash=hash_password("Test123!"))
    db.add(user)
    db.flush()
    return user


def _make_alert(db, asset: Asset, risk_score: float = 50.0, status: AlertStatus = AlertStatus.OPEN) -> Alert:
    alert = Alert(
        title="Test alert",
        source="wazuh",
        source_type="endpoint",
        severity=AlertSeverity.HIGH,
        status=status,
        risk_score=risk_score,
        asset=asset,
        explainability=[],
        recommendations=[],
        tags=[],
        raw_payload={},
        parsed_payload={},
    )
    db.add(alert)
    db.flush()
    return alert


# ──────────────────────────────────────────────────────────────────────────────
# Incident reference uniqueness
# ──────────────────────────────────────────────────────────────────────────────

def test_incident_references_are_unique(client, analyst_token):
    """Two concurrent POSTs to /incidents should produce different reference IDs."""
    payload = {
        "title": "Duplicate reference test",
        "priority": "P3",
        "linked_alert_ids": [],
        "evidence": [],
    }

    r1 = client.post("/api/v1/incidents", headers={"Authorization": f"Bearer {analyst_token}"}, json=payload)
    r2 = client.post("/api/v1/incidents", headers={"Authorization": f"Bearer {analyst_token}"}, json=payload)

    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text
    ref1 = r1.json()["reference"]
    ref2 = r2.json()["reference"]
    assert ref1 != ref2, f"Duplicate reference IDs: {ref1}"


def test_incident_reference_format(client, analyst_token):
    payload = {"title": "Ref format test", "priority": "P2", "linked_alert_ids": [], "evidence": []}
    r = client.post("/api/v1/incidents", headers={"Authorization": f"Bearer {analyst_token}"}, json=payload)
    assert r.status_code == 201
    ref = r.json()["reference"]
    # e.g. INC-20260403-0001
    assert ref.startswith("INC-"), f"Unexpected reference format: {ref}"


# ──────────────────────────────────────────────────────────────────────────────
# Asset risk SQL aggregation
# ──────────────────────────────────────────────────────────────────────────────

def test_refresh_asset_risk_sql_path():
    """_refresh_asset_risk with db param should use SQL aggregation and not touch asset.alerts."""
    with SessionLocal() as db:
        asset = Asset(hostname="sql-test-host", criticality=3, risk_score=0)
        db.add(asset)
        db.flush()

        # Add two open alerts at 60 and 80
        _make_alert(db, asset, risk_score=60.0)
        _make_alert(db, asset, risk_score=80.0)
        db.flush()

        _refresh_asset_risk(asset, db)

        # avg=70, bonus=min(20, 2*0.5)=1 → 71
        assert asset.risk_score == pytest.approx(71.0, abs=1.0)
        assert "2 active" in asset.risk_summary

        db.rollback()


def test_refresh_asset_risk_resolved_alerts_excluded():
    """Resolved alerts should not contribute to asset risk score."""
    with SessionLocal() as db:
        asset = Asset(hostname="resolved-alert-host", criticality=3, risk_score=99.0)
        db.add(asset)
        db.flush()

        _make_alert(db, asset, risk_score=90.0, status=AlertStatus.RESOLVED)
        db.flush()

        _refresh_asset_risk(asset, db)

        assert asset.risk_score == 0.0
        assert asset.risk_summary == "No active alert pressure."

        db.rollback()


# ──────────────────────────────────────────────────────────────────────────────
# Response action status is "recorded"
# ──────────────────────────────────────────────────────────────────────────────

def test_response_action_status_is_recorded(client, analyst_token):
    create_alert_r = client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={
            "title": "Recorded action test",
            "source": "suricata",
            "severity": "high",
            "asset_hostname": "test-endpoint-01",
            "asset_ip": "10.0.0.99",
            "tags": [],
            "raw_payload": {"src_ip": "198.51.100.1"},
            "parsed_payload": {"src_ip": "198.51.100.1"},
        },
    )
    assert create_alert_r.status_code == 201
    alert_id = create_alert_r.json()["id"]

    r = client.post(
        f"/api/v1/alerts/{alert_id}/respond",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"action": "block_ip"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "recorded", f"Expected 'recorded', got '{r.json()['status']}'"
    assert r.json()["execution_mode"] == "recorded"
    assert r.json()["execution_provider"] is None


# ──────────────────────────────────────────────────────────────────────────────
# Integration test endpoint
# ──────────────────────────────────────────────────────────────────────────────

def test_integration_test_returns_structure_for_lab_integrations(client, analyst_token, monkeypatch):
    """Lab-only integrations should remain import-only and skip remote probes entirely."""
    class UnexpectedClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("Import-only integrations should not open an HTTP client for connection tests")

    monkeypatch.setattr(integration_service.httpx, "Client", UnexpectedClient)

    r = client.post(
        "/api/v1/integrations/nmap/test",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "import_only"
    assert body["reachable"] is None


def test_integration_test_returns_not_configured_when_no_url(client, analyst_token, admin_token):
    """Wazuh without a configured URL should return not_configured."""
    client.patch(
        "/api/v1/integrations/wazuh",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"endpoint_url": None},
    )

    r = client.post(
        "/api/v1/integrations/wazuh/test",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "not_configured"
    assert body["reachable"] is False


def test_integration_test_returns_probe_metadata_for_sync_integrations(client, admin_token, analyst_token, monkeypatch):
    """Sync-capable defensive integrations should use the saved config for a lightweight probe."""
    calls: dict[str, dict] = {}

    class FakeResponse:
        def __init__(self, status_code: int):
            self.status_code = status_code

    class FakeStreamResponse(FakeResponse):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeClient:
        def __init__(self, *args, **kwargs):
            calls["client"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def head(self, url, headers=None, auth=None, params=None):
            calls["head"] = {
                "url": url,
                "headers": headers or {},
                "auth": auth,
                "params": params or {},
            }
            return FakeResponse(405)

        def stream(self, method, url, headers=None, auth=None, params=None):
            calls["stream"] = {
                "method": method,
                "url": url,
                "headers": headers or {},
                "auth": auth,
                "params": params or {},
            }
            return FakeStreamResponse(204)

    monkeypatch.setattr(integration_service.httpx, "Client", FakeClient)

    update = client.patch(
        "/api/v1/integrations/suricata",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "endpoint_url": "https://suricata.lab.local/eve/export",
            "auth_type": "bearer",
            "api_token": "demo-token",
            "verify_tls": False,
            "timeout_seconds": 9,
            "lookback_minutes": 30,
            "request_headers": {"X-Cluster": "alpha"},
            "query_params": {"tenant": "blue"},
        },
    )
    assert update.status_code == 200

    r = client.post(
        "/api/v1/integrations/suricata/test",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["reachable"] is True
    assert body["status"] == "ok"
    assert body["http_status"] == 204
    assert body["latency_ms"] is not None
    assert calls["client"]["timeout"] == 9
    assert calls["client"]["verify"] is False
    assert calls["head"]["headers"]["Authorization"] == "Bearer demo-token"
    assert calls["head"]["headers"]["X-Cluster"] == "alpha"
    assert calls["head"]["headers"]["X-AegisCore-Connection-Test"] == "true"
    assert calls["head"]["params"]["tenant"] == "blue"
    assert "since" in calls["head"]["params"]
    assert calls["stream"]["method"] == "GET"
    assert calls["stream"]["headers"]["Range"] == "bytes=0-0"


def test_integration_test_unreachable_returns_error_not_500(client, admin_token, analyst_token, monkeypatch):
    """A configured but unreachable URL should return 200 with reachable=False, not a 500."""
    class FailingClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def head(self, url, headers=None, auth=None, params=None):
            raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(integration_service.httpx, "Client", FailingClient)

    client.patch(
        "/api/v1/integrations/wazuh",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"endpoint_url": "http://192.0.2.1:9200", "timeout_seconds": 2},
    )

    r = client.post(
        "/api/v1/integrations/wazuh/test",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["reachable"] is False
    assert body["status"] == "error"
    assert "latency_ms" in body


def test_integrations_list_detail_and_history_routes_work_after_import(client, admin_token):
    """Integrations should expose list, detail, and history views after a recorded import run."""
    xml_payload = """
    <nmaprun startstr="2026-03-29T10:00:00Z">
      <host>
        <status state="up" />
        <address addr="10.10.10.5" addrtype="ipv4" />
        <hostnames><hostname name="lab-gateway-01" /></hostnames>
        <ports>
          <port protocol="tcp" portid="22">
            <state state="open" />
            <service name="ssh" />
          </port>
        </ports>
      </host>
    </nmaprun>
    """.strip()

    imported = client.post(
        "/api/v1/integrations/nmap/import",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("lab-nmap.xml", xml_payload, "application/xml")},
    )
    assert imported.status_code == 202

    listed = client.get("/api/v1/integrations", headers={"Authorization": f"Bearer {admin_token}"})
    assert listed.status_code == 200
    assert any(item["slug"] == "nmap" for item in listed.json()["items"])

    detail = client.get("/api/v1/integrations/nmap", headers={"Authorization": f"Bearer {admin_token}"})
    assert detail.status_code == 200
    assert detail.json()["configuration"]["lab_only_import"] is True

    history = client.get("/api/v1/integrations/nmap/history", headers={"Authorization": f"Bearer {admin_token}"})
    assert history.status_code == 200
    assert history.json()["total"] >= 1
    assert history.json()["items"][0]["mode"] == "import"


# ──────────────────────────────────────────────────────────────────────────────
# In-memory rate limiter fallback
# ──────────────────────────────────────────────────────────────────────────────

def test_in_memory_rate_limiter_blocks_after_limit():
    limiter = _InMemoryRateLimiter()
    for _ in range(5):
        result = limiter.hit("test-ns", "key1", limit=5, window_seconds=60)
        assert result is None

    blocked = limiter.hit("test-ns", "key1", limit=5, window_seconds=60)
    assert blocked is not None and blocked > 0


def test_in_memory_rate_limiter_resets_on_reset():
    limiter = _InMemoryRateLimiter()
    for _ in range(5):
        limiter.hit("test-ns", "key2", limit=5, window_seconds=60)

    limiter.reset("test-ns", "key2")
    result = limiter.hit("test-ns", "key2", limit=5, window_seconds=60)
    assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# Audit log for retrain job
# ──────────────────────────────────────────────────────────────────────────────

def test_retrain_queued_creates_audit_entry(client, admin_token):
    """Queueing a retrain job should produce a ml.retrain_queued audit entry."""
    with patch("app.services.jobs.get_queue") as mock_get_queue:
        mock_queue = MagicMock()
        mock_get_queue.return_value = mock_queue

        r = client.post("/api/v1/ml/retrain", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 202

        audit = client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"action": "ml.retrain_queued"},
        )
        assert audit.status_code == 200
        assert audit.json()["total"] >= 1


def test_retrain_returns_service_unavailable_when_queue_is_offline(client, admin_token):
    """POST /ml/retrain should fail cleanly when the background queue is unavailable."""
    with patch("app.services.jobs.get_queue", side_effect=RuntimeError("redis unavailable")):
        response = client.post("/api/v1/ml/retrain", headers={"Authorization": f"Bearer {admin_token}"})

    assert response.status_code == 503
    assert "background processing" in response.json()["detail"].lower()


# ──────────────────────────────────────────────────────────────────────────────
# Asset-scoped alert and incident filtering
# ──────────────────────────────────────────────────────────────────────────────

def _create_alert_with_asset(client, token, hostname, ip="10.0.0.1"):
    """Helper: create an alert that auto-creates or reuses an asset."""
    r = client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": f"Alert for {hostname}",
            "source": "wazuh",
            "severity": "high",
            "asset_hostname": hostname,
            "asset_ip": ip,
            "tags": [],
            "raw_payload": {},
            "parsed_payload": {},
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_alerts_filter_by_asset_id(client, analyst_token):
    """GET /alerts?asset_id=... should return only alerts for that asset."""
    a1 = _create_alert_with_asset(client, analyst_token, "host-alpha", "10.0.0.1")
    _create_alert_with_asset(client, analyst_token, "host-beta", "10.0.0.2")

    asset_id = a1["asset"]["id"]
    r = client.get(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {analyst_token}"},
        params={"asset_id": asset_id},
    )
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    assert all(item["asset"]["id"] == asset_id for item in items)


def test_alerts_filter_by_risk_min(client, analyst_token):
    """GET /alerts?risk_min=... should return only alerts at or above the requested score."""
    high = _create_alert_with_asset(client, analyst_token, "host-risk-high", "10.0.0.10")
    low = _create_alert_with_asset(client, analyst_token, "host-risk-low", "10.0.0.11")

    with SessionLocal() as db:
        high_alert = db.query(Alert).filter(Alert.id == high["id"]).one()
        low_alert = db.query(Alert).filter(Alert.id == low["id"]).one()
        high_alert.risk_score = 82.0
        low_alert.risk_score = 24.0
        db.commit()

    response = client.get(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {analyst_token}"},
        params={"risk_min": 65},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert any(item["id"] == high["id"] for item in items)
    assert all(item["risk_score"] >= 65 for item in items)
    assert all(item["id"] != low["id"] for item in items)


def test_incidents_filter_by_linked_asset_id(client, analyst_token):
    """GET /incidents?linked_asset_id=... should return only incidents linked to that asset."""
    a1 = _create_alert_with_asset(client, analyst_token, "host-gamma", "10.0.0.3")
    a2 = _create_alert_with_asset(client, analyst_token, "host-delta", "10.0.0.4")

    # Create incident linked to alert on host-gamma
    inc1 = client.post(
        "/api/v1/incidents",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"title": "Incident gamma", "priority": "P2", "linked_alert_ids": [a1["id"]], "evidence": []},
    )
    assert inc1.status_code == 201

    # Create incident linked to alert on host-delta
    inc2 = client.post(
        "/api/v1/incidents",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"title": "Incident delta", "priority": "P3", "linked_alert_ids": [a2["id"]], "evidence": []},
    )
    assert inc2.status_code == 201

    asset_id = a1["asset"]["id"]
    r = client.get(
        "/api/v1/incidents",
        headers={"Authorization": f"Bearer {analyst_token}"},
        params={"linked_asset_id": asset_id},
    )
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Incident gamma"


# ──────────────────────────────────────────────────────────────────────────────
# Profile update flow
# ──────────────────────────────────────────────────────────────────────────────

def test_profile_update_and_me_reflects_change(client, analyst_token):
    """PATCH /auth/profile should update full_name; GET /auth/me should reflect it."""
    r = client.patch(
        "/api/v1/auth/profile",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"full_name": "Updated Analyst Name"},
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "Updated Analyst Name"

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {analyst_token}"})
    assert me.status_code == 200
    assert me.json()["full_name"] == "Updated Analyst Name"


# ──────────────────────────────────────────────────────────────────────────────
# Alert and incident status updates
# ──────────────────────────────────────────────────────────────────────────────

def test_alert_status_update(client, analyst_token):
    """PATCH /alerts/{id} should update status and return the updated alert."""
    alert = _create_alert_with_asset(client, analyst_token, "status-test-host")

    r = client.patch(
        f"/api/v1/alerts/{alert['id']}",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"status": "triaged"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "triaged"


def test_alert_assignment_can_be_set_and_cleared(client, analyst_token):
    """PATCH /alerts/{id} should support assigning and clearing an analyst owner."""
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {analyst_token}"})
    assert me.status_code == 200
    analyst_id = me.json()["id"]

    alert = _create_alert_with_asset(client, analyst_token, "assignment-test-host")

    assign = client.patch(
        f"/api/v1/alerts/{alert['id']}",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"assigned_to_id": analyst_id},
    )
    assert assign.status_code == 200
    assert assign.json()["assignee"]["id"] == analyst_id

    clear = client.patch(
        f"/api/v1/alerts/{alert['id']}",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"assigned_to_id": None},
    )
    assert clear.status_code == 200
    assert clear.json()["assignee"] is None


def test_incident_status_update_and_timeline_event(client, analyst_token):
    """PATCH /incidents/{id} with status change should record a timeline event."""
    alert = _create_alert_with_asset(client, analyst_token, "incident-status-host")
    inc = client.post(
        "/api/v1/incidents",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"title": "Status transition test", "priority": "P3", "linked_alert_ids": [alert["id"]], "evidence": []},
    )
    assert inc.status_code == 201
    inc_id = inc.json()["id"]

    r = client.patch(
        f"/api/v1/incidents/{inc_id}",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"status": "contained"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "contained"
    # A status-change timeline event should exist
    events = r.json()["timeline_events"]
    status_events = [e for e in events if e["event_type"] == "status-change"]
    assert len(status_events) >= 1


def test_incident_resolution_notes_and_assignee_can_be_updated(client, analyst_token):
    """PATCH /incidents/{id} should support resolution notes and nullable assignee updates."""
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {analyst_token}"})
    assert me.status_code == 200
    analyst_id = me.json()["id"]

    alert = _create_alert_with_asset(client, analyst_token, "incident-resolution-host")
    inc = client.post(
        "/api/v1/incidents",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={
            "title": "Resolution notes test",
            "priority": "P2",
            "assignee_id": analyst_id,
            "linked_alert_ids": [alert["id"]],
            "evidence": [],
        },
    )
    assert inc.status_code == 201
    inc_id = inc.json()["id"]

    update = client.patch(
        f"/api/v1/incidents/{inc_id}",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"resolution_notes": "Containment validated and monitoring continues.", "assignee_id": None},
    )
    assert update.status_code == 200
    assert update.json()["resolution_notes"] == "Containment validated and monitoring continues."
    assert update.json()["assignee"] is None


def test_asset_detail_returns_expected_context(client, analyst_token):
    """GET /assets/{id} should return the asset created from alert telemetry."""
    alert = _create_alert_with_asset(client, analyst_token, "asset-detail-host", "10.20.30.40")
    asset_id = alert["asset"]["id"]

    asset = client.get(
        f"/api/v1/assets/{asset_id}",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert asset.status_code == 200
    body = asset.json()
    assert body["id"] == asset_id
    assert body["hostname"] == "asset-detail-host"
    assert body["ip_address"] == "10.20.30.40"
