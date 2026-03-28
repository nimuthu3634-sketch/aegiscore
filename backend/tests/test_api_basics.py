from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_reports_expected_metadata() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()

    assert payload["app_name"] == "AegisCore"
    assert payload["environment"] == "development"
    assert payload["version"] == "0.1.0"
    assert payload["database"] in {"connected", "unavailable"}
    assert payload["redis"] in {"connected", "unavailable"}
    assert payload["status"] in {"ok", "degraded"}


def test_public_self_registration_is_disabled_by_default() -> None:
    response = client.post(
        "/auth/register",
        json={
            "full_name": "New Student",
            "email": "student@aegiscore.local",
            "password": "password",
            "role": "viewer",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Self-registration is disabled for this deployment."
    }
