from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_aegiscore.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["JWT_SECRET_KEY"] = "test-secret"

from app.core.config import get_settings

get_settings.cache_clear()

from app.core.security import hash_password
from app.db.base import Base
from app.db.init_db import ensure_default_integrations
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.entities import ModelMetadata, User, UserRole
from app.ml.scoring import train_model


def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
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
    reset_database()
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token(client: TestClient) -> str:
    response = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "Admin123!"})
    return response.json()["access_token"]


@pytest.fixture
def analyst_token(client: TestClient) -> str:
    response = client.post("/api/v1/auth/login", json={"email": "analyst@example.com", "password": "Analyst123!"})
    return response.json()["access_token"]
