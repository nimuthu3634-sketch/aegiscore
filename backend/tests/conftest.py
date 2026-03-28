import pytest

from app.services import alerts as alerts_service
from app.services import incidents as incidents_service
from app.services import integrations as integrations_service
from app.services import logs as logs_service
from app.services import response_actions as response_actions_service
from app.services import users as users_service


@pytest.fixture(autouse=True)
def isolate_api_tests_from_running_postgres(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    if "sqlite_storage" in request.fixturenames:
        return

    def run_without_db(operation, fallback):
        return fallback()

    monkeypatch.setattr(alerts_service, "run_with_optional_db", run_without_db)
    monkeypatch.setattr(incidents_service, "run_with_optional_db", run_without_db)
    monkeypatch.setattr(integrations_service, "run_with_optional_db", run_without_db)
    monkeypatch.setattr(logs_service, "run_with_optional_db", run_without_db)
    monkeypatch.setattr(response_actions_service, "run_with_optional_db", run_without_db)
    monkeypatch.setattr(users_service, "run_with_optional_db", run_without_db)
