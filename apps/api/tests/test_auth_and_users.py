from __future__ import annotations

from passlib.hash import pbkdf2_sha256

from app.db.session import SessionLocal
from app.models.entities import User, UserRole


def test_login_sets_secure_session_cookie_and_me_supports_cookie_auth(client, login_as):
    response = login_as("admin@example.com", "Admin123!")

    assert response.status_code == 200
    assert response.cookies.get("auth_token")
    assert response.cookies.get("auth_role") == "Admin"
    assert response.headers["cache-control"] == "no-store"

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"


def test_logout_clears_session_cookie(client, login_as):
    login = login_as("admin@example.com", "Admin123!")

    assert login.status_code == 200
    assert client.cookies.get("auth_token")

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 204
    assert client.cookies.get("auth_token") is None
    assert client.cookies.get("auth_role") is None


def test_logout_clears_invalid_session_cookie(client):
    client.cookies.set("auth_token", "invalid-token")
    client.cookies.set("auth_role", "Admin")

    logout = client.post("/api/v1/auth/logout")

    assert logout.status_code == 204
    set_cookie_headers = logout.headers.get_list("set-cookie")
    assert any("auth_token=" in header and ("Max-Age=0" in header or "expires=" in header.lower()) for header in set_cookie_headers)
    assert any("auth_role=" in header and ("Max-Age=0" in header or "expires=" in header.lower()) for header in set_cookie_headers)


def test_login_and_me(client):
    response = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "Admin123!"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["role"] == "Admin"

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {payload['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"


def test_login_supports_legacy_pbkdf2_hash_and_rehashes_password(client):
    with SessionLocal() as db:
        user = User(
            email="legacy-analyst@example.com",
            full_name="Legacy Analyst",
            role=UserRole.ANALYST,
            password_hash=pbkdf2_sha256.hash("Legacy123!"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "legacy-analyst@example.com", "password": "Legacy123!"},
    )

    assert response.status_code == 200
    with SessionLocal() as db:
        migrated_user = db.get(User, user_id)
        assert migrated_user is not None
        assert migrated_user.password_hash.startswith("$2")


def test_admin_can_create_user(client, admin_token):
    response = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "new-analyst@example.com",
            "full_name": "New Analyst",
            "role": "Analyst",
            "password": "NewAnalyst123!",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "new-analyst@example.com"


def test_admin_cannot_create_user_with_weak_password(client, admin_token):
    response = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "weak-password@example.com",
            "full_name": "Weak Password User",
            "role": "Analyst",
            "password": "password",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"] == "Validation failed"
    assert payload["request_id"]


def test_authenticated_user_can_list_users(client, analyst_token):
    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {analyst_token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 3
    assert any(user["email"] == "admin@example.com" for user in payload["items"])


def test_viewer_cannot_list_users(client, viewer_token):
    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {viewer_token}"})

    assert response.status_code == 403


def test_login_rate_limit_triggers_after_repeated_failures(client):
    headers = {"X-Forwarded-For": "198.51.100.25"}
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "WrongPassword123!"},
            headers=headers,
        )
        assert response.status_code == 401

    limited = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "WrongPassword123!"},
        headers=headers,
    )

    assert limited.status_code == 429
    assert limited.headers["retry-after"]
    assert limited.json()["request_id"]
