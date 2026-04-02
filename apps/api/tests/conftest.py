from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["JWT_SECRET_KEY"] = "test-secret"

API_ROOT = Path(__file__).resolve().parents[1]
TEST_DB_PATH = Path(__file__).resolve().parents[3] / "test_aegiscore.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.config import get_settings

get_settings.cache_clear()

from app.core.rate_limit import reset_rate_limits
from app.core.security import hash_password
from app.db.base import Base
from app.db.init_db import ensure_default_integrations
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.entities import ModelMetadata, User, UserRole
from app.ml.scoring import train_model


def reset_database() -> None:
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_default_integrations(db)
        admin = User(
            email="admin@example.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
            password_hash=hash_password("Admin123!"),
        )
        analyst = User(
            email="analyst@example.com",
            full_name="Analyst User",
            role=UserRole.ANALYST,
            password_hash=hash_password("Analyst123!"),
        )
        viewer = User(
            email="viewer@example.com",
            full_name="Viewer User",
            role=UserRole.VIEWER,
            password_hash=hash_password("Viewer123!"),
        )
        db.add_all([admin, analyst, viewer])
        db.commit()
        if db.query(ModelMetadata).count() == 0:
            train_model(db, "test-seed")


@pytest.fixture(autouse=True)
def bootstrap_database() -> Generator[None, None, None]:
    reset_rate_limits()
    reset_database()
    yield
    engine.dispose()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def login_as(client: TestClient):
    def _login_as(email: str, password: str, *, ip_address: str = "203.0.113.10"):
        return client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            headers={"X-Forwarded-For": ip_address},
        )

    return _login_as


@pytest.fixture
def auth_headers():
    def _auth_headers(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers


@pytest.fixture
def admin_token(login_as) -> str:
    response = login_as("admin@example.com", "Admin123!")
    return response.json()["access_token"]


@pytest.fixture
def analyst_token(login_as) -> str:
    response = login_as("analyst@example.com", "Analyst123!")
    return response.json()["access_token"]


@pytest.fixture
def viewer_token(login_as) -> str:
    response = login_as("viewer@example.com", "Viewer123!")
    return response.json()["access_token"]
