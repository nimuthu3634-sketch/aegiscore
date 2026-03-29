from __future__ import annotations


def test_login_and_me(client):
    response = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "Admin123!"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["role"] == "Admin"

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {payload['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"


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
